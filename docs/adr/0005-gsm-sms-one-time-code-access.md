# ADR-0005: Remote entry by SMS one-time code via an indoor GSM modem

Status: accepted for architecture v2, 2026-10-07.

## Context

The owner does not want an outdoor keypad or RFID reader. Remote entry should work from an ordinary phone over the mobile network, independent of Internet, cloud, Home Assistant and the outdoor P4. Caller ID and SMS sender addresses are spoofable, SMS is not end-to-end confidential, and message bodies persist in phones, backups and operator systems. ADR-0002 and `protocol/access.md` already forbid caller ID as a sole main-door credential. A static code sent by SMS stops being secret after its first use.

## Decision

1. A cellular modem is attached **indoors** to the access controller MCU, never to the P4 or the outdoor enclosure. It is a new principal kind, `AC_PRINCIPAL_GSM`, handled by `ac_handle_sms()`; it cannot obtain an ACR1 challenge and P4/keypad principals cannot use the SMS path.
2. The **sender number is only a filter**. The modem adapter drops messages from numbers not on the indoor allowlist without reply, and maps an allowed number to its principal ID and key.
3. The **credential is an LSMS1 one-time code** (`protocol/sms-access.md`): 8 digits, HMAC-SHA-256 over a per-principal counter, the logical resource ID and the command, truncated as in RFC 4226. Binding resource and command means an intercepted, undelivered code cannot be redirected to another door or action.
4. **Counter, not time.** SMS delivery can be delayed by minutes; a counter needs no clock on the phone or controller. The controller accepts the next 20 counter values and durably stores `matched + 1` **before** actuation; replays and older codes are dead.
5. The SMS path reuses the existing per-principal attempt limit, lockout, busy, resource-profile and actuator checks. All of them run **before** the code is verified, so a refused attempt never consumes a counter value.
6. Codes are generated on the phone by `tools/loon_sms.py`, standard-library Python that runs in a-Shell (iOS, callable from Shortcuts) or Termux (Android). iOS Shortcuts has no native HMAC action; this avoids an app store or vendor dependency. A printed list of precomputed codes is an acceptable fallback.
7. Use an LTE Cat-1 (or later) modem with SMS support. 2G/3G modules are not acceptable given European network shutdowns; Cat-M/NB-IoT SMS support varies by operator and must be checked before purchase.

## Consequences

Security reduces to the 256-bit per-phone key and the counter's durability. A stolen phone with the key file can open the door until the key is revoked indoors; the phone's own lock screen is the only protection. Revocation and key rotation are indoor provisioning operations. Codes are 8 digits within a 20-value window, so a blind guess succeeds with probability 2×10⁻⁷ per attempt; with the current lockout (3 failures, 30 s) a sender-spoofing attacker would need on the order of 10⁶ SMS per expected success. The existing lockout does not escalate; WP4 should add escalating backoff and a daily ceiling before deployment. The controller must not reply with success/failure details to unknown numbers. The modem, SIM subscription (prepaid cards in Portugal expire without top-up), antenna placement and indoor power are new integration gates. Counter persistence adds one bounded flash write per successful entry.

## Rejected alternatives

Caller ID alone, static PINs in SMS, and time-based codes (TOTP) that would fail under delayed delivery or need trusted clocks on both ends. Outdoor keypad and RFID are out of scope by owner decision; ACR1 keeps the keypad principal kinds for a possible later module.
