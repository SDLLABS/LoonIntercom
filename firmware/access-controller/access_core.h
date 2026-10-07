#ifndef SDLLABS_ACCESS_CORE_H
#define SDLLABS_ACCESS_CORE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Portable policy core. No board pin, network, clock, storage or crypto driver. */
#define AC_FRAME_LEN 122u
#define AC_SIGNED_LEN 90u
#define AC_CHALLENGE_LEN 16u
#define AC_MAX_PRINCIPALS 4u
#define AC_CHALLENGE_TTL_MS 5000u
#define AC_RETRY_MS 1000u
#define AC_LOCKOUT_MS 30000u
/* Provisional software safety ceilings, not production actuator timings. */
#define AC_MAX_RESOURCE_ID 16u
#define AC_MAX_PULSE_MS 1000u
#define AC_MAX_CUTOFF_MS 1500u

struct ac_actuator_profile {
    uint8_t actuator_id; /* Indoor-only identifier; never read from the frame. */
    uint32_t pulse_ms;
    uint32_t cutoff_ms;
};

enum ac_profile_lookup { AC_PROFILE_FOUND, AC_PROFILE_UNKNOWN, AC_PROFILE_ERROR };

enum ac_principal_kind { AC_PRINCIPAL_P4 = 1, AC_PRINCIPAL_DIRECT_KEYPAD = 2,
                         AC_PRINCIPAL_GSM = 3 };

/* SMS path (ADR-0005): command codes bound into the one-time code. */
#define AC_SMS_CODE_DIGITS 8u
enum ac_sms_command { AC_SMS_OPEN = 1 };
enum ac_result {
    AC_OK = 0, AC_MALFORMED, AC_UNCONFIDENTIAL, AC_PEER_MISMATCH, AC_UNKNOWN_PRINCIPAL,
    AC_NO_CHALLENGE, AC_EXPIRED, AC_REPLAY, AC_AUTH_FAILED,
    AC_RATE_LIMITED, AC_CLASS_DENIED, AC_UNKNOWN_RESOURCE, AC_PROFILE_FAILED,
    AC_UNSAFE_PROFILE, AC_CREDENTIAL_DENIED,
    AC_BUSY, AC_HARDWARE_FAULT
};

struct ac_callbacks {
    /* Must consult an indoor provisioned allowlist; never trust packet labels. */
    bool (*principal_kind)(void *user, const uint8_t principal[8],
                           enum ac_principal_kind *kind);
    /* CSPRNG; returns false if entropy is unavailable. */
    bool (*random16)(void *user, uint8_t out[AC_CHALLENGE_LEN]);
    /* Verify HMAC-SHA-256 over exactly AC_SIGNED_LEN bytes using an indoor key.
       Must reject unknown/revoked key IDs and compare tags in constant time. */
    bool (*verify_mac)(void *user, const uint8_t principal[8], uint8_t key_id,
                       const uint8_t frame[AC_SIGNED_LEN],
                       const uint8_t tag[32]);
    /* Protected indoor configuration maps logical resource to actuator and timing.
       No untrusted frame byte may be used directly as an actuator identifier. */
    enum ac_profile_lookup (*lookup_profile)(void *user, uint8_t resource_id,
                                              struct ac_actuator_profile *out);
    /* Payload is sensitive and valid only during this call. No log or retention.
       Adapter verifies credential, resource scope, validity/usage and revocation.
       A one-time grant is consumed on authorization, before physical actuation. */
    bool (*verify_credential)(void *user, const uint8_t principal[8],
                              const uint8_t credential_id[8],
                              const uint8_t payload[32], uint8_t credential_class,
                              uint8_t resource_id);
    /* Independent hardware cutoff, capable of dropping output if MCU stalls. */
    bool (*arm_cutoff)(void *user, uint32_t maximum_ms);
    /* Must force the independent cutoff into its de-energized safe state,
       including if set_relay(false) fails. Never bypass the safety cutoff. */
    bool (*force_cutoff_off)(void *user);
    /* All outputs off at boot/fault, including an unidentified prior actuator. */
    bool (*force_relays_off)(void *user);
    /* Actuator ID comes only from a validated indoor profile. Board must be
       electrically off before firmware starts. */
    bool (*set_relay)(void *user, uint8_t actuator_id, bool energized);
    /* Optional; NULL disables the SMS path. Verifies an LSMS1 one-time code
       for this GSM principal, resource and command, and on success durably
       advances that principal's counter BEFORE returning true. Must return
       false if the counter cannot be persisted. Called only after rate
       limit, busy and resource-profile checks have passed. */
    bool (*verify_sms_otp)(void *user, const uint8_t principal[8],
                           uint8_t resource_id, uint8_t command,
                           const char code[AC_SMS_CODE_DIGITS]);
};

struct ac_slot {
    uint8_t principal[8];
    uint8_t challenge[AC_CHALLENGE_LEN];
    uint64_t issued_ms;
    uint64_t retry_after_ms;
    uint64_t lock_until_ms;
    uint8_t failures;
    bool used;
    bool challenge_active;
};

struct ac_controller {
    struct ac_callbacks cb;
    void *user;
    struct ac_slot slots[AC_MAX_PRINCIPALS];
    uint64_t relay_deadline_ms;
    uint32_t active_pulse_ms;
    uint8_t active_actuator_id;
    bool relay_on;
    bool fault_latched;
};

bool ac_init(struct ac_controller *controller, const struct ac_callbacks *callbacks,
             void *user);
enum ac_result ac_issue_challenge(struct ac_controller *controller,
                                  const uint8_t authenticated_peer[8],
                                  bool authenticated_confidential_channel,
                                  uint64_t now_ms,
                                  uint8_t out[AC_CHALLENGE_LEN]);
enum ac_result ac_handle_request(struct ac_controller *controller,
                                 const uint8_t *frame, size_t len,
                                 const uint8_t authenticated_peer[8],
                                 bool authenticated_confidential_channel,
                                 uint64_t now_ms);
/* SMS entry point for an indoor GSM modem adapter. principal is the indoor
   allowlist identity the adapter resolved from the sender number; the sender
   number itself is only a filter, never the credential. */
enum ac_result ac_handle_sms(struct ac_controller *controller,
                             const uint8_t principal[8], uint8_t resource_id,
                             uint8_t command, const char code[AC_SMS_CODE_DIGITS],
                             uint64_t now_ms);
void ac_tick(struct ac_controller *controller, uint64_t now_ms);
void ac_fault(struct ac_controller *controller);

#endif
