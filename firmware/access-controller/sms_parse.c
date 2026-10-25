#include "sms_parse.h"

#include <string.h>

static bool is_space(char c) { return c == ' ' || c == '\r' || c == '\n'; }
static bool is_digit(char c) { return c >= '0' && c <= '9'; }
static char upper(char c) { return (c >= 'a' && c <= 'z') ? (char)(c - 32) : c; }

static bool word_equals(const char *s, size_t n, const char *word)
{
    size_t wn = strlen(word);
    if (n != wn) return false;
    for (size_t i = 0; i < n; ++i)
        if (upper(s[i]) != word[i]) return false;
    return true;
}

bool sms_parse(const char *body, size_t len, struct sms_request *out)
{
    if (!body || !out || len == 0 || len > SMS_MAX_BODY) return false;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)body[i];
        if (c < 0x20 && c != '\r' && c != '\n') return false;
        if (c > 0x7e) return false;
    }
    const char *tok[3];
    size_t tlen[3];
    size_t n = 0, i = 0;
    while (i < len) {
        while (i < len && is_space(body[i])) ++i;
        if (i == len) break;
        if (n == 3) return false;
        tok[n] = body + i;
        size_t start = i;
        while (i < len && !is_space(body[i])) ++i;
        tlen[n++] = i - start;
    }
    if (n != 3) return false;

    struct sms_request r;
    memset(&r, 0, sizeof(r));
    if (word_equals(tok[0], tlen[0], "ABRIR") || word_equals(tok[0], tlen[0], "OPEN"))
        r.command = AC_SMS_OPEN;
    else
        return false;

    if (tlen[1] < 1 || tlen[1] > 2 || tok[1][0] == '0') return false;
    unsigned res = 0;
    for (size_t k = 0; k < tlen[1]; ++k) {
        if (!is_digit(tok[1][k])) return false;
        res = res * 10u + (unsigned)(tok[1][k] - '0');
    }
    if (res < 1 || res > AC_MAX_RESOURCE_ID) return false;
    r.resource_id = (uint8_t)res;

    if (tlen[2] != SMS_OTP_DIGITS) return false;
    for (size_t k = 0; k < SMS_OTP_DIGITS; ++k)
        if (!is_digit(tok[2][k])) return false;
    memcpy(r.code, tok[2], SMS_OTP_DIGITS);

    *out = r;
    return true;
}
