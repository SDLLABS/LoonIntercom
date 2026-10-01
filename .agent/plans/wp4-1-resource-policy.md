# WP4.1 execution plan — resource-scoped indoor actuation

## Goal

Make each authenticated access request name a bounded logical resource, then let protected indoor policy select and safely time its actuator before protocol v1 is frozen.

## Non-goals

No production relay, board, transport, credential store, production timing, or physical validation is selected. Bell and P4 firmware are unchanged.

## Constraints

Apply `AGENTS.md`: outdoor never owns relay authority; confidential authenticated transport, peer binding, HMAC, one-shot challenge, replay rejection, class limits, rate limiting, fail-off output, and an independent maximum-on cutoff remain required. Keep parsing fixed-length and bounded.

## Current state

At `2008b9f`, `protocol/access.md` and `firmware/access-controller/access_core.*` define a fixed 121-byte ACR1 frame with a generic entry action and global `AC_PULSE_MS`/`AC_CUTOFF_MS`. At current HEAD, `docs/architecture-v2.md` allocates strike and gate control indoors but does not define the mapping.

## Proposed design

Insert a one-byte, nonzero logical resource ID into ACR1 and keep the frame fixed-length. After authentication, challenge consumption, class/rate and busy checks, the indoor adapter looks up a resource profile. A profile holds an indoor actuator ID and protected pulse/cutoff values. Unknown resources, lookup errors and invalid profiles fail closed before credential consumption. The credential adapter checks authorization for that resource and consumes any one-time grant before hardware actuation. A single actuator can be active; all-output fail-off and independent cutoff remain separate adapter obligations.

## Security analysis

P4, keypad attached to P4, LAN and HA remain untrusted. The resource ID is an authenticated request for a policy decision, never a GPIO, output state or timing. Profile/credential records come from protected indoor configuration. Compile-time ceilings and runtime validation bound pulse and cutoff; hardware independently enforces maximum-on. Authenticated attempts consume a one-shot challenge even when resource policy denies. A one-time grant is spent on an authorized attempt before physical actuation, so an arm/output failure or immobile door does not restore it. No success-of-door-movement claim follows from `AC_OK`.

## Work breakdown

- [x] Review WP4 commit, current architecture and repository instructions.
- [x] Update frame, callbacks and fail-closed policy flow.
- [x] Extend host tests for resource scope, profile failures and timing bounds.
- [x] Update contract, architecture, hardware gates and documentation.
- [x] Run host, sanitizer, documentation/link and whitespace checks.
- [x] Commit one focused WP4.1 change.

## Validation

Run `make -C firmware/access-controller test`, a sanitizer build of that target if supported, a local Markdown link check, and `git diff --check`. No target ESP-IDF build or physical actuator test is possible from this portable skeleton.

## Progress

Implementation and host validation complete; ready for the focused commit.

## Decisions / discoveries

No production resource registry or timing values exist. Test profiles will use illustrative values only. The protocol version 1 layout can still change because it has not been frozen or deployed.

## Final result

ACR1 now has a fixed 122-byte pre-freeze v1 layout with a logical resource ID covered by the MAC. An indoor profile callback selects actuator and timing, validates hard ceilings, and passes the resource to credential policy. All-output fail-off remains explicit. Host tests cover valid/unknown/unauthorized resources, profile lookup errors, unsafe timing, replay and existing negative cases. Normal and AddressSanitizer/UndefinedBehaviorSanitizer host builds passed; changed Markdown links resolve and `git diff --check` passed. ESP-IDF and hardware tests were not run. Production resource registry, timings, transport/crypto/credential adapters, relay/cutoff hardware, key storage and door/REX sensing remain integration gates.
