#include "../access_core.h"

#include <assert.h>
#include <openssl/crypto.h>
#include <openssl/hmac.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static const uint8_t p4_id[8] = {1, 2, 3, 4, 5, 6, 7, 8};
static const uint8_t keypad_id[8] = {8, 7, 6, 5, 4, 3, 2, 1};
enum { TEST_FRONT_RESOURCE = 1, TEST_GATE_RESOURCE = 2,
       TEST_FRONT_ACTUATOR = 7, TEST_GATE_ACTUATOR = 9,
       TEST_PULSE_MS = 250, TEST_CUTOFF_MS = 500 };
static const uint8_t test_key[32] = {0x28, 0xb9, 0xd6, 0x82, 0x31, 0xc5, 0x42, 0x7f,
    0x81, 0x05, 0xe9, 0x33, 0x6b, 0x21, 0x3a, 0x19, 0x51, 0x64, 0x88, 0x94,
    0xa2, 0xf9, 0x3d, 0x9b, 0xd4, 0x41, 0x76, 0x07, 0x5e, 0x35, 0x2b, 0x90};

struct fixture {
    struct ac_controller controller;
    bool output;
    bool cutoff_armed;
    bool fail_arm;
    bool fail_relay_off;
    bool fail_profile;
    bool deny_gate;
    uint8_t active_actuator;
    uint8_t last_resource;
    uint32_t pulse_ms;
    uint32_t cutoff_ms;
    unsigned rng_count;
    unsigned credential_calls;
};

static bool principal_kind(void *user, const uint8_t id[8], enum ac_principal_kind *kind)
{
    (void)user;
    if (memcmp(id, p4_id, 8) == 0) { *kind = AC_PRINCIPAL_P4; return true; }
    if (memcmp(id, keypad_id, 8) == 0) { *kind = AC_PRINCIPAL_DIRECT_KEYPAD; return true; }
    return false;
}

static bool random16(void *user, uint8_t out[16])
{
    struct fixture *f = user;
    ++f->rng_count;
    for (unsigned i = 0; i < 16; ++i) out[i] = (uint8_t)(f->rng_count + i);
    return true;
}

static bool verify_mac(void *user, const uint8_t id[8], uint8_t key_id,
                       const uint8_t frame[AC_SIGNED_LEN], const uint8_t tag[32])
{
    (void)user;
    enum ac_principal_kind kind;
    uint8_t calculated[32];
    unsigned int len = 0;
    if (!principal_kind(user, id, &kind) || key_id != 7) return false;
    if (!HMAC(EVP_sha256(), test_key, sizeof(test_key), frame, AC_SIGNED_LEN,
              calculated, &len) || len != 32) return false;
    bool result = CRYPTO_memcmp(calculated, tag, 32) == 0;
    OPENSSL_cleanse(calculated, sizeof(calculated));
    return result;
}

static enum ac_profile_lookup lookup_profile(void *user, uint8_t resource_id,
                                              struct ac_actuator_profile *out)
{
    struct fixture *f = user;
    if (f->fail_profile) return AC_PROFILE_ERROR;
    if (resource_id != TEST_FRONT_RESOURCE && resource_id != TEST_GATE_RESOURCE)
        return AC_PROFILE_UNKNOWN;
    out->actuator_id = resource_id == TEST_FRONT_RESOURCE ? TEST_FRONT_ACTUATOR : TEST_GATE_ACTUATOR;
    out->pulse_ms = f->pulse_ms;
    out->cutoff_ms = f->cutoff_ms;
    return AC_PROFILE_FOUND;
}

static bool verify_credential(void *user, const uint8_t id[8], const uint8_t cred_id[8],
                              const uint8_t payload[32], uint8_t cred_class,
                              uint8_t resource_id)
{
    struct fixture *f = user;
    (void)id;
    (void)cred_id;
    (void)cred_class;
    ++f->credential_calls;
    f->last_resource = resource_id;
    /* Deliberate fake policy: tests control acceptance, not a PIN design. */
    return payload[0] == 0xa5 && !(f->deny_gate && resource_id == TEST_GATE_RESOURCE);
}

static bool arm_cutoff(void *user, uint32_t max_ms)
{
    struct fixture *f = user;
    assert(max_ms == f->cutoff_ms);
    if (f->fail_arm) return false;
    f->cutoff_armed = true;
    return true;
}

static bool force_cutoff_off(void *user)
{
    ((struct fixture *)user)->cutoff_armed = false;
    return true;
}
static bool force_relays_off(void *user)
{
    struct fixture *f = user;
    f->output = false;
    f->active_actuator = 0;
    return true;
}
static bool set_relay(void *user, uint8_t actuator_id, bool on)
{
    struct fixture *f = user;
    assert(actuator_id == TEST_FRONT_ACTUATOR || actuator_id == TEST_GATE_ACTUATOR);
    assert(!on || f->cutoff_armed);
    if (!on && f->fail_relay_off) return false;
    f->output = on;
    f->active_actuator = on ? actuator_id : 0;
    return true;
}

static void setup(struct fixture *f)
{
    memset(f, 0, sizeof(*f));
    f->pulse_ms = TEST_PULSE_MS;
    f->cutoff_ms = TEST_CUTOFF_MS;
    const struct ac_callbacks cb = {principal_kind, random16, verify_mac,
        lookup_profile, verify_credential, arm_cutoff, force_cutoff_off,
        force_relays_off, set_relay, NULL};
    assert(ac_init(&f->controller, &cb, f));
    assert(!f->output && !f->cutoff_armed);
}

static void frame(struct fixture *f, uint8_t out[AC_FRAME_LEN], const uint8_t id[8],
                  uint8_t cls, uint8_t resource, bool good_credential, uint64_t now_ms)
{
    uint8_t challenge[16];
    assert(ac_issue_challenge(&f->controller, id, true, now_ms, challenge) == AC_OK);
    memset(out, 0, AC_FRAME_LEN);
    memcpy(out, "ACR1", 4);
    out[4] = 1;
    out[5] = 1;
    out[6] = resource;
    out[7] = cls;
    out[8] = 7;
    memcpy(out + 10, id, 8);
    out[18] = (uint8_t)f->rng_count;
    memcpy(out + 34, challenge, 16);
    out[50] = 9;
    out[58] = good_credential ? 0xa5 : 0x51;
    unsigned int len = 0;
    assert(HMAC(EVP_sha256(), test_key, sizeof(test_key), out, AC_SIGNED_LEN,
                out + AC_SIGNED_LEN, &len));
    assert(len == 32);
}

static void test_valid_and_replay(void)
{
    struct fixture f;
    uint8_t request[AC_FRAME_LEN];
    setup(&f);
    frame(&f, request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_OK);
    assert(f.output && f.cutoff_armed);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 102) != AC_OK);
    ac_tick(&f.controller, 350);
    assert(f.output);
    ac_tick(&f.controller, 351);
    assert(!f.output && !f.cutoff_armed);
}

static void test_malformed_and_auth(void)
{
    struct fixture f;
    uint8_t request[AC_FRAME_LEN];
    setup(&f);
    frame(&f, request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request) - 1, p4_id, true, 101) == AC_MALFORMED);
    request[6] = 0;
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_MALFORMED);
    request[6] = AC_MAX_RESOURCE_ID + 1;
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_MALFORMED);
    request[6] = TEST_FRONT_RESOURCE;
    request[9] = 1;
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_MALFORMED);
    request[9] = 0;
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, false, 101) == AC_UNCONFIDENTIAL);
    assert(ac_handle_request(&f.controller, request, sizeof(request), keypad_id, true, 101) == AC_PEER_MISMATCH);
    request[6] = TEST_GATE_RESOURCE;
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_AUTH_FAILED);
    request[6] = TEST_FRONT_RESOURCE;
    request[58] ^= 1;
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_AUTH_FAILED);
    assert(!f.output && f.credential_calls == 0);
}

static void test_resource_policy(void)
{
    struct fixture f;
    uint8_t request[AC_FRAME_LEN];
    setup(&f);
    frame(&f, request, p4_id, 1, TEST_GATE_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_OK);
    assert(f.output && f.active_actuator == TEST_GATE_ACTUATOR);
    assert(f.last_resource == TEST_GATE_RESOURCE);
    ac_tick(&f.controller, 351);
    assert(!f.output && !f.cutoff_armed);

    setup(&f);
    frame(&f, request, p4_id, 1, 3, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_UNKNOWN_RESOURCE);
    assert(f.credential_calls == 0 && !f.output);

    setup(&f);
    f.deny_gate = true;
    frame(&f, request, p4_id, 1, TEST_GATE_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_CREDENTIAL_DENIED);
    assert(f.credential_calls == 1 && f.last_resource == TEST_GATE_RESOURCE && !f.output);

    setup(&f);
    f.fail_profile = true;
    frame(&f, request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_PROFILE_FAILED);
    assert(f.credential_calls == 0 && !f.output);
}

static void test_profile_safety_bounds(void)
{
    const struct { uint32_t pulse_ms, cutoff_ms; } cases[] = {
        {0, TEST_CUTOFF_MS},
        {AC_MAX_PULSE_MS + 1, AC_MAX_CUTOFF_MS},
        {TEST_PULSE_MS, 0},
        {TEST_PULSE_MS, TEST_PULSE_MS},
        {TEST_PULSE_MS, AC_MAX_CUTOFF_MS + 1},
    };
    for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        struct fixture f;
        uint8_t request[AC_FRAME_LEN];
        setup(&f);
        f.pulse_ms = cases[i].pulse_ms;
        f.cutoff_ms = cases[i].cutoff_ms;
        frame(&f, request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
        assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 101) == AC_UNSAFE_PROFILE);
        assert(f.credential_calls == 0 && !f.output && !f.cutoff_armed);
    }
}

static void test_expiry_class_and_lockout(void)
{
    struct fixture f;
    uint8_t request[AC_FRAME_LEN];
    setup(&f);
    frame(&f, request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 5101) == AC_EXPIRED);
    assert(!f.output);
    frame(&f, request, p4_id, 2, TEST_FRONT_RESOURCE, true, 5200);
    assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, 5201) == AC_CLASS_DENIED);
    assert(f.credential_calls == 0);
    for (unsigned i = 0; i < 3; ++i) {
        uint64_t at = 6300 + (uint64_t)i * 1100;
        frame(&f, request, p4_id, 1, TEST_FRONT_RESOURCE, false, at);
        assert(ac_handle_request(&f.controller, request, sizeof(request), p4_id, true, at + 1) == AC_CREDENTIAL_DENIED);
    }
    assert(ac_issue_challenge(&f.controller, p4_id, true, 10000, request) == AC_RATE_LIMITED);
    assert(!f.output);
}

static void test_cutoff_and_direct_keypad(void)
{
    struct fixture f;
    uint8_t request[AC_FRAME_LEN];
    setup(&f);
    frame(&f, request, keypad_id, 2, TEST_FRONT_RESOURCE, true, 100);
    f.fail_arm = true;
    assert(ac_handle_request(&f.controller, request, sizeof(request), keypad_id, true, 101) == AC_HARDWARE_FAULT);
    assert(f.credential_calls == 1); /* Production adapter commits one-time use here. */
    assert(!f.output && f.controller.fault_latched);
    setup(&f);
    frame(&f, request, keypad_id, 2, TEST_FRONT_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request), keypad_id, true, 101) == AC_OK);
    ac_fault(&f.controller);
    assert(!f.output && !f.cutoff_armed && f.controller.fault_latched);
}

static void test_peer_binding_and_stale_signed_frame(void)
{
    struct fixture f;
    uint8_t old_request[AC_FRAME_LEN], current_request[AC_FRAME_LEN], challenge[16];
    setup(&f);
    assert(ac_issue_challenge(&f.controller, p4_id, false, 100, challenge) == AC_UNCONFIDENTIAL);
    assert(f.rng_count == 0);
    frame(&f, old_request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
    frame(&f, current_request, p4_id, 1, TEST_FRONT_RESOURCE, true, 101);
    assert(ac_handle_request(&f.controller, old_request, sizeof(old_request),
                             p4_id, true, 102) == AC_REPLAY);
    assert(ac_handle_request(&f.controller, current_request, sizeof(current_request),
                             keypad_id, true, 102) == AC_PEER_MISMATCH);
    assert(ac_handle_request(&f.controller, current_request, sizeof(current_request),
                             p4_id, true, 102) == AC_OK);
    assert(f.output);
}

static void test_busy_does_not_consume_credential(void)
{
    struct fixture f;
    uint8_t p4_request[AC_FRAME_LEN], keypad_request[AC_FRAME_LEN];
    setup(&f);
    frame(&f, p4_request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, p4_request, sizeof(p4_request),
                             p4_id, true, 101) == AC_OK);
    assert(f.credential_calls == 1);
    frame(&f, keypad_request, keypad_id, 2, TEST_FRONT_RESOURCE, true, 102);
    assert(ac_handle_request(&f.controller, keypad_request, sizeof(keypad_request),
                             keypad_id, true, 103) == AC_BUSY);
    assert(f.credential_calls == 1);
}

static void test_failed_relay_off_forces_independent_cutoff(void)
{
    struct fixture f;
    uint8_t request[AC_FRAME_LEN];
    setup(&f);
    frame(&f, request, p4_id, 1, TEST_FRONT_RESOURCE, true, 100);
    assert(ac_handle_request(&f.controller, request, sizeof(request),
                             p4_id, true, 101) == AC_OK);
    f.fail_relay_off = true;
    ac_tick(&f.controller, 351);
    assert(f.output); /* Failed GPIO deassertion in the mock. */
    assert(!f.cutoff_armed); /* Independent cutoff removed physical power. */
    assert(f.controller.fault_latched);
}

int main(void)
{
    test_valid_and_replay();
    test_malformed_and_auth();
    test_resource_policy();
    test_profile_safety_bounds();
    test_expiry_class_and_lockout();
    test_cutoff_and_direct_keypad();
    test_peer_binding_and_stale_signed_frame();
    test_busy_does_not_consume_credential();
    test_failed_relay_off_forces_independent_cutoff();
    puts("access_core: all host tests passed");
    return 0;
}
