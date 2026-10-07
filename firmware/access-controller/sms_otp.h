#ifndef SDLLABS_SMS_OTP_H
#define SDLLABS_SMS_OTP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* LSMS1 one-time codes: counter-based, HOTP-style (RFC 4226 dynamic
   truncation) but HMAC-SHA-256 over a message that also binds the logical
   resource and command, so an intercepted code cannot be reused to ask for
   a different action. See protocol/sms-access.md. Portable: no allocation,
   no storage, no crypto library; the caller supplies HMAC-SHA-256. */

#define SMS_OTP_DIGITS 8u
#define SMS_OTP_WINDOW 20u      /* look-ahead for codes generated but not sent */
#define SMS_OTP_DOMAIN "LOON-SMS1"
#define SMS_OTP_DOMAIN_LEN 9u
#define SMS_OTP_MSG_LEN (SMS_OTP_DOMAIN_LEN + 8u + 1u + 1u)

typedef bool (*sms_hmac_sha256_fn)(void *user, const uint8_t *key, size_t key_len,
                                   const uint8_t *msg, size_t msg_len,
                                   uint8_t out[32]);

/* Writes SMS_OTP_DIGITS ASCII digits plus NUL. Returns false on HMAC failure. */
bool sms_otp_code(sms_hmac_sha256_fn hmac, void *user,
                  const uint8_t *key, size_t key_len, uint64_t counter,
                  uint8_t resource_id, uint8_t command,
                  char out[SMS_OTP_DIGITS + 1u]);

enum sms_otp_result { SMS_OTP_MATCH, SMS_OTP_NO_MATCH, SMS_OTP_ERROR };

/* Checks counters [next_counter, next_counter + SMS_OTP_WINDOW). Every
   candidate is computed and compared in constant time; no early exit.
   On SMS_OTP_MATCH, *matched is the lowest matching counter. The caller must
   durably store *matched + 1 as the new next_counter BEFORE authorising. */
enum sms_otp_result sms_otp_verify(sms_hmac_sha256_fn hmac, void *user,
                                   const uint8_t *key, size_t key_len,
                                   uint64_t next_counter,
                                   uint8_t resource_id, uint8_t command,
                                   const char code[SMS_OTP_DIGITS],
                                   uint64_t *matched);

#endif
