#include "sms_otp.h"

#include <string.h>

static void wipe(void *p, size_t n)
{
    volatile uint8_t *b = p;
    while (n--) *b++ = 0;
}

static bool compute(sms_hmac_sha256_fn hmac, void *user, const uint8_t *key,
                    size_t key_len, uint64_t counter, uint8_t resource_id,
                    uint8_t command, char out[SMS_OTP_DIGITS + 1u])
{
    uint8_t msg[SMS_OTP_MSG_LEN];
    uint8_t mac[32];
    memcpy(msg, SMS_OTP_DOMAIN, SMS_OTP_DOMAIN_LEN);
    for (unsigned i = 0; i < 8; ++i)
        msg[SMS_OTP_DOMAIN_LEN + i] = (uint8_t)(counter >> (56u - 8u * i));
    msg[SMS_OTP_DOMAIN_LEN + 8u] = resource_id;
    msg[SMS_OTP_DOMAIN_LEN + 9u] = command;
    bool ok = hmac(user, key, key_len, msg, sizeof(msg), mac);
    if (ok) {
        unsigned off = mac[31] & 0x0fu;
        uint32_t bin = ((uint32_t)(mac[off] & 0x7fu) << 24) |
                       ((uint32_t)mac[off + 1] << 16) |
                       ((uint32_t)mac[off + 2] << 8) | mac[off + 3];
        bin %= 100000000u; /* 10^SMS_OTP_DIGITS */
        for (int i = (int)SMS_OTP_DIGITS - 1; i >= 0; --i) {
            out[i] = (char)('0' + bin % 10u);
            bin /= 10u;
        }
        out[SMS_OTP_DIGITS] = '\0';
    }
    wipe(mac, sizeof(mac));
    return ok;
}

bool sms_otp_code(sms_hmac_sha256_fn hmac, void *user, const uint8_t *key,
                  size_t key_len, uint64_t counter, uint8_t resource_id,
                  uint8_t command, char out[SMS_OTP_DIGITS + 1u])
{
    if (!hmac || !key || !key_len || !out) return false;
    return compute(hmac, user, key, key_len, counter, resource_id, command, out);
}

enum sms_otp_result sms_otp_verify(sms_hmac_sha256_fn hmac, void *user,
                                   const uint8_t *key, size_t key_len,
                                   uint64_t next_counter, uint8_t resource_id,
                                   uint8_t command, const char code[SMS_OTP_DIGITS],
                                   uint64_t *matched)
{
    if (!hmac || !key || !key_len || !code || !matched) return SMS_OTP_ERROR;
    if (next_counter > UINT64_MAX - SMS_OTP_WINDOW) return SMS_OTP_ERROR;
    bool found = false;
    uint64_t first = 0;
    char candidate[SMS_OTP_DIGITS + 1u];
    for (uint64_t c = next_counter; c < next_counter + SMS_OTP_WINDOW; ++c) {
        if (!compute(hmac, user, key, key_len, c, resource_id, command, candidate)) {
            wipe(candidate, sizeof(candidate));
            return SMS_OTP_ERROR;
        }
        uint8_t diff = 0;
        for (unsigned i = 0; i < SMS_OTP_DIGITS; ++i)
            diff |= (uint8_t)(candidate[i] ^ code[i]);
        bool hit = diff == 0;
        if (hit && !found) first = c;
        found |= hit;
    }
    wipe(candidate, sizeof(candidate));
    if (!found) return SMS_OTP_NO_MATCH;
    *matched = first;
    return SMS_OTP_MATCH;
}
