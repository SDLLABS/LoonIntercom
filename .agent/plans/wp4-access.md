# WP4 execution plan — indoor access boundary

## Goal

Define and host-test a bounded authenticated access request and a safe indoor controller core that alone may decide to pulse an actuator.

## Non-goals

No board, keypad, network transport, provisioning system, production crypto adapter, relay circuit, or deployable indoor firmware is selected or implemented. No changes to the bell or P4 firmware.

## Constraints

Apply `AGENTS.md`: indoor-only relay authority, authenticated replay-resistant short-lived requests, no plaintext PIN storage/logging, keypad rate limiting, no direct HA/MQTT relay path, fail-off output and independent maximum-on cutoff. Preserve the independent bell. Outdoor P4 is physically untrusted and may see any PIN attached to it.

## Current state

`docs/architecture-v2.md` and ADR-0002 allocate access verification and actuators indoors. `protocol/access.md`, `firmware/access-controller/`, and `hardware/access-controller/` do not yet exist. The OpenChime Ring signed-command language is a requirement, not implemented protocol code; no source will be copied.

## Proposed design

Use a controller-issued 128-bit challenge with a five-second monotonic deadline and one active challenge per principal. A fixed-length versioned request authenticates the exact frame with a 256-bit MAC. The controller consumes a challenge after successful authentication, before credential policy, so even rejected credentials cannot be replayed. PIN material is permitted only inside an authenticated confidential transport and passed to a credential-policy adapter without logging or persistence. The core keeps bounded indoor attempt state across P4 restarts. A policy success first arms an independent cutoff, then asserts the relay for a shorter firmware pulse; fault/reset goes off.

## Security analysis

The P4, LAN, HA and media stack are untrusted. A valid P4 MAC proves only its provisioned identity, not physical user authorization; indoor credential policy is mandatory. A P4 keypad may reveal entered PINs to compromised P4 firmware; only scoped convenience credentials are eligible on that path. A separate direct protected keypad path is needed for higher assurance, with hardware unresolved. Unknown keys, malformed frames, unconfidential channels, stale/replayed challenges, failed policy, lockout and cutoff-arm failure all deny. Challenge generation requires a controller CSPRNG and volatile state; controller reboot invalidates all challenges. Provisioning, persistent credential protection, RTC validity for temporary grants, and independent cutoff hardware remain integration gates.

## Work breakdown

- [x] Read repository instructions, handoff, v2 architecture, provenance and ADRs.
- [x] Define wire, challenge, credential assurance and actuator contracts.
- [x] Add host-testable parser, verifier, rate limiter and relay state machine.
- [x] Test malformed, expired, replayed and unsafe-output paths; run available checks.
- [x] Document hardware gates and final result.

## Validation

Run `make -C firmware/access-controller test`, `git diff --check`, and review document links. No ESP-IDF target or board exists, so no target build or hardware test is possible. Physical relay cutoff, brownout behavior, contact welding, egress and key storage require later hardware validation.

## Progress

Host-testable contract, core and hardware gates are written. The root agent will review and commit alongside the parallel WP2/WP3 work.

## Decisions / discoveries

An indoor challenge avoids trusting P4 wall time and repeated flash counter writes. A request MAC alone does not conceal a PIN on the LAN, so the API rejects requests unless its transport marks the session authenticated and confidential. The authenticated transport peer is an explicit argument to both challenge and request APIs; mismatched frame identity denies. The challenge is consumed before policy to prevent repeated credential attempts with one authenticated frame. A stale signed request is rejected without consuming the current challenge or locking its principal, avoiding an unauthenticated replay-based lockout. Network replay traffic still needs a transport-level rate bound.

## Final result

Added `protocol/access.md`, the portable `firmware/access-controller/` core and host tests, and `hardware/access-controller/README.md`. The core uses a fixed 121-byte frame, HMAC verification adapter, five-second one-shot indoor challenge, principal rate limit, class gate, credential-policy callback, safe relay state machine and independent cutoff interface. Busy actuators reject before potentially consuming one-time credentials; the independent cutoff is forced off before relay-off, including when that operation fails. `make -C firmware/access-controller test` passed with normal and AddressSanitizer/UndefinedBehaviorSanitizer builds; Markdown links, new-file whitespace and `git diff --check` passed. ESP-IDF build, real cryptographic/credential adapter, relay circuit and all hardware checks were not run. Integration risks remain transport peer binding implementation, production key/RTC/credential storage and revocation, cutoff/egress design, and P4 PIN exposure. No actuator or keypad hardware is selected.

The subsequent [WP4.1 resource-policy plan](wp4-1-resource-policy.md) revises the pre-freeze frame and indoor actuator contract; the 121-byte layout above is historical to WP4 at `2008b9f`.
