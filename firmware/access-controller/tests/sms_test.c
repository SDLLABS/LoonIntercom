#include "../access_core.h"
#include "../sms_otp.h"
#include "../sms_parse.h"

#include <assert.h>
#include <openssl/hmac.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

_Static_assert(SMS_OTP_DIGITS == AC_SMS_CODE_DIGITS, "code length must agree");

static const uint8_t gsm_id[8] = {0x47, 0x53, 0x4d, 0, 0, 0, 0, 1};
static const uint8_t p4_id[8] = {1, 2, 3, 4, 5, 6, 7, 8};
static uint8_t key[32]; /* 00 01 .. 1f, same as tools/loon_sms.py vectors */

enum { RES_FRONT = 1, RES_GATE = 2, ACT_FRONT = 7, ACT_GATE = 9 };

struct fixture {
    struct ac_controller c;
    uint64_t next_counter;  /* models the durable per-principal counter */
    bool fail_persist;
    bool output;
    bool cutoff;
    uint8_t active;
    unsigned otp_calls;
};

static bool hmac_sha256(void *user, const uint8_t *k, size_t kl, const uint8_t *m,
                        size_t ml, uint8_t out[32])
{
    (void)user;
    unsigned int len = 0;
    return HMAC(EVP_sha256(), k, (int)kl, m, ml, out, &len) && len == 32;
}

static bool principal_kind(void *u, const uint8_t id[8], enum ac_principal_kind *k)
{
    (void)u;
    if (!memcmp(id, gsm_id, 8)) { *k = AC_PRINCIPAL_GSM; return true; }
    if (!memcmp(id, p4_id, 8)) { *k = AC_PRINCIPAL_P4; return true; }
    return false;
}
static bool random16(void *u, uint8_t o[16]) { (void)u; memset(o, 0x5a, 16); return true; }
static bool verify_mac(void *u, const uint8_t p[8], uint8_t k, const uint8_t f[AC_SIGNED_LEN],
                       const uint8_t t[32]) { (void)u; (void)p; (void)k; (void)f; (void)t; return false; }
static enum ac_profile_lookup lookup(void *u, uint8_t r, struct ac_actuator_profile *o)
{
    (void)u;
    if (r != RES_FRONT && r != RES_GATE) return AC_PROFILE_UNKNOWN;
    o->actuator_id = r == RES_FRONT ? ACT_FRONT : ACT_GATE;
    o->pulse_ms = 250;
    o->cutoff_ms = 500;
    return AC_PROFILE_FOUND;
}
static bool verify_cred(void *u, const uint8_t p[8], const uint8_t i[8], const uint8_t pl[32],
                        uint8_t cl, uint8_t r) { (void)u; (void)p; (void)i; (void)pl; (void)cl; (void)r; return false; }
static bool arm(void *u, uint32_t ms) { (void)ms; ((struct fixture *)u)->cutoff = true; return true; }
static bool cut_off(void *u) { ((struct fixture *)u)->cutoff = false; return true; }
static bool all_off(void *u) { struct fixture *f = u; f->output = false; f->active = 0; return true; }
static bool relay(void *u, uint8_t a, bool on)
{
    struct fixture *f = u;
    assert(!on || f->cutoff);
    f->output = on;
    f->active = on ? a : 0;
    return true;
}

/* Reference adapter: what the indoor glue must do. */
static bool verify_otp(void *u, const uint8_t p[8], uint8_t r, uint8_t cmd,
                       const char code[AC_SMS_CODE_DIGITS])
{
    struct fixture *f = u;
    ++f->otp_calls;
    if (memcmp(p, gsm_id, 8)) return false;
    uint64_t matched;
    if (sms_otp_verify(hmac_sha256, NULL, key, sizeof(key), f->next_counter, r, cmd,
                       code, &matched) != SMS_OTP_MATCH)
        return false;
    if (f->fail_persist) return false; /* cannot persist: fail closed */
    f->next_counter = matched + 1;    /* durable write happens here */
    return true;
}

static void setup(struct fixture *f, bool sms_enabled)
{
    memset(f, 0, sizeof(*f));
    struct ac_callbacks cb = {principal_kind, random16, verify_mac, lookup, verify_cred,
                              arm, cut_off, all_off, relay,
                              sms_enabled ? verify_otp : NULL};
    assert(ac_init(&f->c, &cb, f));
}

static void gen(uint64_t counter, uint8_t res, char out[9])
{
    assert(sms_otp_code(hmac_sha256, NULL, key, sizeof(key), counter, res, AC_SMS_OPEN, out));
}

static enum ac_result sms(struct fixture *f, const char *body, uint64_t now)
{
    struct sms_request r;
    if (!sms_parse(body, strlen(body), &r)) return AC_MALFORMED;
    return ac_handle_sms(&f->c, gsm_id, r.resource_id, r.command, r.code, now);
}

static void test_vectors(void)
{
    /* Cross-checked with: tools/loon_sms.py vector 0001..1f COUNTER RESOURCE */
    static const struct { uint64_t c; uint8_t r; const char *code; } v[] = {
        {0, 1, "98063282"}, {1, 1, "70864653"}, {5, 1, "91312245"},
        {0, 2, "91961607"}, {19, 1, "24605791"}, {20, 1, "28166278"}};
    char out[9];
    for (size_t i = 0; i < sizeof(v) / sizeof(v[0]); ++i) {
        gen(v[i].c, v[i].r, out);
        assert(!strcmp(out, v[i].code));
    }
}

static void test_parse(void)
{
    struct sms_request r;
    assert(sms_parse("ABRIR 1 98063282", 16, &r) && r.resource_id == 1 &&
           r.command == AC_SMS_OPEN && !memcmp(r.code, "98063282", 8));
    assert(sms_parse("  open  16   12345678\r\n", 23, &r) && r.resource_id == 16);
    const char *bad[] = {"", "ABRIR", "ABRIR 1", "ABRIR 1 1234567", "ABRIR 1 123456789",
                         "ABRIR 0 12345678", "ABRIR 01 12345678", "ABRIR 17 12345678",
                         "FECHAR 1 12345678", "ABRIR 1 1234567x", "ABRIR 1 12345678 X",
                         "ABRIR\t1 12345678", "ABRIR 1 12345678 ............................"};
    for (size_t i = 0; i < sizeof(bad) / sizeof(bad[0]); ++i)
        assert(!sms_parse(bad[i], strlen(bad[i]), &r));
    const char nonascii[] = "ABR\xc3\x8dR 1 12345678";
    assert(!sms_parse(nonascii, strlen(nonascii), &r));
}

static void test_open_and_replay(void)
{
    struct fixture f;
    setup(&f, true);
    assert(sms(&f, "ABRIR 1 98063282", 1000) == AC_OK);
    assert(f.output && f.active == ACT_FRONT && f.next_counter == 1);
    ac_tick(&f.c, 1250);
    assert(!f.output && !f.cutoff);
    /* Same SMS again (replay): counter already consumed. */
    assert(sms(&f, "ABRIR 1 98063282", 3000) == AC_CREDENTIAL_DENIED);
    assert(!f.output && f.next_counter == 1);
}

static void test_window(void)
{
    struct fixture f;
    char code[9], body[32];
    setup(&f, true);
    gen(5, RES_FRONT, code); /* phone generated 0..4 but never sent them */
    snprintf(body, sizeof body, "ABRIR 1 %s", code);
    assert(sms(&f, body, 1000) == AC_OK && f.next_counter == 6);
    ac_tick(&f.c, 2000);
    gen(3, RES_FRONT, code); /* older code is now dead */
    snprintf(body, sizeof body, "ABRIR 1 %s", code);
    assert(sms(&f, body, 3000) == AC_CREDENTIAL_DENIED);
    /* Exactly at the edge: next=6, window covers 6..25; 26 is outside. */
    gen(26, RES_FRONT, code);
    snprintf(body, sizeof body, "ABRIR 1 %s", code);
    assert(sms(&f, body, 5000) == AC_CREDENTIAL_DENIED && f.next_counter == 6);
    gen(25, RES_FRONT, code);
    snprintf(body, sizeof body, "ABRIR 1 %s", code);
    assert(sms(&f, body, 7000) == AC_OK && f.next_counter == 26);
}

static void test_resource_binding(void)
{
    struct fixture f;
    setup(&f, true);
    /* Code generated for resource 1 cannot open resource 2. */
    assert(sms(&f, "ABRIR 2 98063282", 1000) == AC_CREDENTIAL_DENIED);
    assert(!f.output && f.next_counter == 0);
    assert(sms(&f, "ABRIR 2 91961607", 3000) == AC_OK && f.active == ACT_GATE);
}

static void test_principals(void)
{
    struct fixture f;
    uint8_t ch[16];
    const uint8_t stranger[8] = {9, 9, 9, 9, 9, 9, 9, 9};
    setup(&f, true);
    assert(ac_handle_sms(&f.c, p4_id, 1, AC_SMS_OPEN, "98063282", 1000) == AC_UNKNOWN_PRINCIPAL);
    assert(ac_handle_sms(&f.c, stranger, 1, AC_SMS_OPEN, "98063282", 1000) == AC_UNKNOWN_PRINCIPAL);
    /* The GSM principal cannot use the network request path. */
    assert(ac_issue_challenge(&f.c, gsm_id, true, 1000, ch) == AC_UNKNOWN_PRINCIPAL);
    assert(f.otp_calls == 0 && !f.output);
}

static void test_no_consume_before_checks(void)
{
    struct fixture f;
    setup(&f, true);
    assert(sms(&f, "ABRIR 3 12345678", 1000) == AC_UNKNOWN_RESOURCE);
    assert(f.otp_calls == 0);
    assert(sms(&f, "ABRIR 1 98063282", 1500) == AC_RATE_LIMITED); /* 1 s spacing */
    assert(f.otp_calls == 0 && f.next_counter == 0);
    assert(sms(&f, "ABRIR 1 98063282", 2500) == AC_OK);
    /* While the relay is on, a valid next code is BUSY and not consumed. */
    assert(sms(&f, "ABRIR 1 70864653", 3600) == AC_BUSY);
    ac_tick(&f.c, 3700);
    assert(f.next_counter == 1);
    assert(sms(&f, "ABRIR 1 70864653", 4700) == AC_OK);
}

static void test_lockout(void)
{
    struct fixture f;
    setup(&f, true);
    assert(sms(&f, "ABRIR 1 00000001", 1000) == AC_CREDENTIAL_DENIED);
    assert(sms(&f, "ABRIR 1 00000002", 2000) == AC_CREDENTIAL_DENIED);
    assert(sms(&f, "ABRIR 1 00000003", 3000) == AC_CREDENTIAL_DENIED);
    unsigned calls = f.otp_calls;
    /* Valid code during lockout: refused and NOT consumed. */
    assert(sms(&f, "ABRIR 1 98063282", 10000) == AC_RATE_LIMITED);
    assert(f.otp_calls == calls && f.next_counter == 0);
    assert(sms(&f, "ABRIR 1 98063282", 3000 + AC_LOCKOUT_MS) == AC_OK);
}

static void test_fail_closed(void)
{
    struct fixture f;
    setup(&f, true);
    f.fail_persist = true;
    assert(sms(&f, "ABRIR 1 98063282", 1000) == AC_CREDENTIAL_DENIED && !f.output);
    setup(&f, false);
    assert(sms(&f, "ABRIR 1 98063282", 1000) == AC_CLASS_DENIED && !f.output);
    setup(&f, true);
    assert(ac_handle_sms(&f.c, gsm_id, 1, AC_SMS_OPEN, "9806328x", 1000) == AC_MALFORMED);
    assert(ac_handle_sms(&f.c, gsm_id, 1, 2, "98063282", 1000) == AC_MALFORMED);
    ac_fault(&f.c);
    assert(sms(&f, "ABRIR 1 98063282", 2000) == AC_HARDWARE_FAULT && f.otp_calls == 0);
}

int main(void)
{
    for (unsigned i = 0; i < 32; ++i) key[i] = (uint8_t)i;
    test_vectors();
    test_parse();
    test_open_and_replay();
    test_window();
    test_resource_binding();
    test_principals();
    test_no_consume_before_checks();
    test_lockout();
    test_fail_closed();
    puts("sms: all host tests passed");
    return 0;
}
