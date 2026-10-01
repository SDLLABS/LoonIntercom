#include "access_core.h"

#include <string.h>

_Static_assert(AC_MAX_RESOURCE_ID > 0 && AC_MAX_RESOURCE_ID <= UINT8_MAX,
               "resource ID ceiling must fit the wire field");
_Static_assert(AC_MAX_PULSE_MS > 0 && AC_MAX_PULSE_MS < AC_MAX_CUTOFF_MS,
               "software pulse ceiling must be below cutoff ceiling");

static uint64_t deadline(uint64_t now_ms, uint64_t delta_ms)
{
    return UINT64_MAX - now_ms < delta_ms ? UINT64_MAX : now_ms + delta_ms;
}

static bool all_zero(const uint8_t *bytes, size_t len)
{
    uint8_t any = 0;
    for (size_t i = 0; i < len; ++i) any |= bytes[i];
    return any == 0;
}

static bool equal_bytes(const uint8_t *a, const uint8_t *b, size_t len)
{
    uint8_t diff = 0;
    for (size_t i = 0; i < len; ++i) diff |= (uint8_t)(a[i] ^ b[i]);
    return diff == 0;
}

static struct ac_slot *find_slot(struct ac_controller *c, const uint8_t principal[8])
{
    for (size_t i = 0; i < AC_MAX_PRINCIPALS; ++i) {
        if (c->slots[i].used && equal_bytes(c->slots[i].principal, principal, 8))
            return &c->slots[i];
    }
    return NULL;
}

static struct ac_slot *allocate_slot(struct ac_controller *c, const uint8_t principal[8])
{
    struct ac_slot *slot = find_slot(c, principal);
    if (slot) return slot;
    for (size_t i = 0; i < AC_MAX_PRINCIPALS; ++i) {
        slot = &c->slots[i];
        if (!slot->used) {
            memset(slot, 0, sizeof(*slot));
            memcpy(slot->principal, principal, 8);
            slot->used = true;
            return slot;
        }
    }
    return NULL; /* Full allowlist: fail closed; no eviction of rate state. */
}

bool ac_init(struct ac_controller *c, const struct ac_callbacks *cb, void *user)
{
    if (!c || !cb || !cb->principal_kind || !cb->random16 || !cb->verify_mac ||
        !cb->lookup_profile || !cb->verify_credential || !cb->arm_cutoff ||
        !cb->force_cutoff_off || !cb->force_relays_off || !cb->set_relay)
        return false;
    memset(c, 0, sizeof(*c));
    c->cb = *cb;
    c->user = user;
    bool cutoff_safe = c->cb.force_cutoff_off(user);
    bool relay_safe = c->cb.force_relays_off(user);
    c->fault_latched = !cutoff_safe || !relay_safe;
    return !c->fault_latched;
}

enum ac_result ac_issue_challenge(struct ac_controller *c,
                                  const uint8_t authenticated_peer[8], bool confidential,
                                  uint64_t now_ms, uint8_t out[AC_CHALLENGE_LEN])
{
    enum ac_principal_kind kind;
    if (!c || !authenticated_peer || !out || c->fault_latched) return AC_HARDWARE_FAULT;
    if (!confidential) return AC_UNCONFIDENTIAL;
    if (!c->cb.principal_kind(c->user, authenticated_peer, &kind) ||
        (kind != AC_PRINCIPAL_P4 && kind != AC_PRINCIPAL_DIRECT_KEYPAD))
        return AC_UNKNOWN_PRINCIPAL;
    struct ac_slot *slot = allocate_slot(c, authenticated_peer);
    if (!slot) return AC_RATE_LIMITED;
    if (now_ms < slot->retry_after_ms || now_ms < slot->lock_until_ms)
        return AC_RATE_LIMITED;
    /* Never erase attempt or lockout state when replacing a lost challenge. */
    slot->challenge_active = false;
    if (!c->cb.random16(c->user, slot->challenge) ||
        all_zero(slot->challenge, AC_CHALLENGE_LEN)) return AC_HARDWARE_FAULT;
    slot->issued_ms = now_ms;
    slot->challenge_active = true;
    memcpy(out, slot->challenge, AC_CHALLENGE_LEN);
    return AC_OK;
}

static void record_failure(struct ac_slot *slot, uint64_t now_ms)
{
    if (slot->failures < 3) ++slot->failures;
    slot->retry_after_ms = deadline(now_ms, AC_RETRY_MS);
    if (slot->failures >= 3) {
        slot->lock_until_ms = deadline(now_ms, AC_LOCKOUT_MS);
        slot->failures = 0;
    }
}

enum ac_result ac_handle_request(struct ac_controller *c, const uint8_t *f, size_t len,
                                 const uint8_t authenticated_peer[8], bool confidential,
                                 uint64_t now_ms)
{
    if (!c || !f || !authenticated_peer || c->fault_latched) return AC_HARDWARE_FAULT;
    if (len != AC_FRAME_LEN || memcmp(f, "ACR1", 4) || f[4] != 1 ||
        f[5] != 1 || f[6] == 0 || f[6] > AC_MAX_RESOURCE_ID ||
        (f[7] != 1 && f[7] != 2) || f[9] != 0 ||
        all_zero(f + 18, 16) || all_zero(f + 50, 8))
        return AC_MALFORMED;
    if (!confidential) return AC_UNCONFIDENTIAL;
    if (!equal_bytes(authenticated_peer, f + 10, 8)) return AC_PEER_MISMATCH;
    enum ac_principal_kind kind;
    if (!c->cb.principal_kind(c->user, f + 10, &kind) ||
        (kind != AC_PRINCIPAL_P4 && kind != AC_PRINCIPAL_DIRECT_KEYPAD))
        return AC_UNKNOWN_PRINCIPAL;
    struct ac_slot *slot = find_slot(c, f + 10);
    if (!slot || !slot->challenge_active) return AC_NO_CHALLENGE;
    if (now_ms < slot->issued_ms || now_ms - slot->issued_ms > AC_CHALLENGE_TTL_MS) {
        slot->challenge_active = false;
        return AC_EXPIRED;
    }
    if (!c->cb.verify_mac(c->user, f + 10, f[8], f, f + AC_SIGNED_LEN))
        return AC_AUTH_FAILED;
    /* A stale signed frame must not invalidate or lock out the current challenge. */
    if (!equal_bytes(slot->challenge, f + 34, AC_CHALLENGE_LEN)) return AC_REPLAY;
    /* This is a one-shot challenge even when policy later refuses the attempt. */
    slot->challenge_active = false;
    if (now_ms < slot->retry_after_ms || now_ms < slot->lock_until_ms)
        return AC_RATE_LIMITED;
    slot->retry_after_ms = deadline(now_ms, AC_RETRY_MS);
    if (f[7] == 2 && kind != AC_PRINCIPAL_DIRECT_KEYPAD)
        return AC_CLASS_DENIED;
    /* Credential verification may consume a one-time grant; reject busy first. */
    if (c->relay_on) return AC_BUSY;
    struct ac_actuator_profile profile = {0};
    enum ac_profile_lookup lookup = c->cb.lookup_profile(c->user, f[6], &profile);
    if (lookup == AC_PROFILE_UNKNOWN) return AC_UNKNOWN_RESOURCE;
    if (lookup != AC_PROFILE_FOUND) return AC_PROFILE_FAILED;
    if (!profile.actuator_id || !profile.pulse_ms ||
        profile.pulse_ms > AC_MAX_PULSE_MS ||
        profile.cutoff_ms <= profile.pulse_ms ||
        profile.cutoff_ms > AC_MAX_CUTOFF_MS)
        return AC_UNSAFE_PROFILE;
    if (!c->cb.verify_credential(c->user, f + 10, f + 50, f + 58, f[7], f[6])) {
        record_failure(slot, now_ms);
        return AC_CREDENTIAL_DENIED;
    }
    slot->failures = 0;
    if (!c->cb.arm_cutoff(c->user, profile.cutoff_ms)) {
        ac_fault(c);
        return AC_HARDWARE_FAULT;
    }
    if (!c->cb.set_relay(c->user, profile.actuator_id, true)) {
        ac_fault(c);
        return AC_HARDWARE_FAULT;
    }
    c->relay_on = true;
    c->active_actuator_id = profile.actuator_id;
    c->active_pulse_ms = profile.pulse_ms;
    c->relay_deadline_ms = deadline(now_ms, profile.pulse_ms);
    return AC_OK;
}

void ac_fault(struct ac_controller *c)
{
    if (!c) return;
    c->fault_latched = true;
    c->relay_on = false;
    c->relay_deadline_ms = 0;
    c->active_pulse_ms = 0;
    c->active_actuator_id = 0;
    c->cb.force_cutoff_off(c->user);
    c->cb.force_relays_off(c->user);
}

void ac_tick(struct ac_controller *c, uint64_t now_ms)
{
    if (!c || !c->relay_on) return;
    if (now_ms >= c->relay_deadline_ms ||
        c->relay_deadline_ms - now_ms > c->active_pulse_ms) {
        uint8_t actuator_id = c->active_actuator_id;
        c->relay_on = false;
        c->relay_deadline_ms = 0;
        bool cutoff_safe = c->cb.force_cutoff_off(c->user);
        bool relay_safe = c->cb.set_relay(c->user, actuator_id, false);
        c->active_actuator_id = 0;
        c->active_pulse_ms = 0;
        if (!cutoff_safe || !relay_safe) c->fault_latched = true;
    }
}
