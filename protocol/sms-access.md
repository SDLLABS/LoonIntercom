# LSMS1: SMS one-time-code access (host-testable)

Status: host-testable contract; governed by [ADR-0005](../docs/adr/0005-gsm-sms-one-time-code-access.md) and [ADR-0002](../docs/adr/0002-indoor-only-relay-authority.md). Not deployable until the gates below are met.

## Message

Plain ASCII SMS body, at most 40 bytes:

```
ABRIR <resource> <code>
```

- `ABRIR` (or `OPEN`), case-insensitive. Only command: `1` = request entry.
- `<resource>`: decimal `1`–`16`, no leading zero. Indoor policy maps it to an actuator profile, exactly as in ACR1.
- `<code>`: exactly 8 ASCII digits.
- Tokens are separated by spaces; leading/trailing spaces, CR and LF are ignored. Tabs, extra tokens, non-ASCII and anything else are rejected (`firmware/access-controller/sms_parse.c`).

## Code

```
msg  = "LOON-SMS1" || counter (uint64, big-endian) || resource (uint8) || command (uint8)   ; 19 bytes
mac  = HMAC-SHA-256(key, msg)                                                              ; key: 32 random bytes per phone
off  = mac[31] & 0x0f
code = ((mac[off] & 0x7f) << 24 | mac[off+1] << 16 | mac[off+2] << 8 | mac[off+3]) mod 10^8, zero-padded to 8 digits
```

Reference implementations: `firmware/access-controller/sms_otp.c` and `tools/loon_sms.py` (test vectors in `tests/sms_test.c`, key `00 01 … 1f`: counter 0, resource 1 → `98063282`).

## Verification order (indoor)

1. Modem adapter: sender number (operator-normalised E.164, exact match) must be on the indoor allowlist; otherwise drop silently. Map it to principal ID and key. Wipe the SMS from modem storage after reading.
2. Parse the body strictly; reject on any deviation.
3. `ac_handle_sms()`: principal must be `AC_PRINCIPAL_GSM`; then attempt spacing/lockout, busy actuator and resource profile safety. **None of these consumes a code.**
4. `verify_sms_otp` adapter: compare against counters `next … next+19` in constant time. On a match, durably store `matched + 1`; if that write fails, deny.
5. On success, arm the independent cutoff and pulse the indoor actuator, as in ACR1. Failures count toward lockout.

## Phone side

`tools/loon_sms.py init` creates `~/.loon-sms.json` (key + counter, mode 0600); `key` prints the key for indoor provisioning; `next -r 1` advances the counter **before** printing `ABRIR 1 xxxxxxxx`. Up to 19 generated-but-unsent codes are tolerated; beyond that, resynchronise by provisioning.

- iOS: a-Shell's "Execute Command" Shortcuts action runs `python3 loon_sms.py next`, and a "Send Message" action sends the output to the modem's number.
- Android: Termux (+ Termux:Widget) runs the same script and `termux-sms-send -n <number>`.

## Integration gates

- Select the LTE Cat-1 modem, SIM plan and antenna; confirm SMS on the chosen operator.
- Protected key storage and provisioning/revocation per phone; durable, power-loss-safe counter storage.
- Escalating lockout and daily ceiling per principal; a global SMS rate limit against flooding.
- Optional reply SMS only to allowlisted senders, without failure reasons.
- Everything listed under ACR1 integration gates for the cutoff, relays and actuator timing.
