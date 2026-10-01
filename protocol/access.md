# Indoor access request protocol v1 (WP4 skeleton)

Status: host-testable contract; **not deployable until the integration gates below are met**. No OpenChime source or wire format is used. [Architecture v2](../docs/architecture-v2.md) and [ADR-0002](../docs/adr/0002-indoor-only-relay-authority.md) govern authority.

## Boundary and credential assurance

The protected indoor controller is the only device with relay and strike/gate power wiring. The outdoor P4 can request a policy decision for a logical resource but never names a GPIO, actuator ID, relay state, pulse duration or cutoff duration. HA, MQTT, NVR and Caller ID cannot directly unlock. A P4-connected keypad is physically untrusted: compromised P4 firmware can observe PIN entry. Indoor verification protects the relay from direct wiring attacks but cannot keep such a PIN secret. P4 principals may request only **convenience** credentials whose time, use count, resource scope and revocation are bounded by indoor policy. A separate direct secure keypad/controller could request a **higher-assurance** credential without exposing entry to P4; its protected wiring and hardware are undecided. A P4 key must never be provisioned as a direct-keypad principal.

The 32-byte credential payload is opaque to the protocol core and sensitive. An indoor credential adapter must verify a stored keyed/password verifier, not plaintext PIN, and enforce not-before, expiry, remaining uses, requested-resource scope and revocation. One-time use consumption must be atomic and durable on an authorized attempt **before** physical actuation. A failed cutoff arm, failed relay command, or door that does not move does not restore that use; `AC_OK` means the pulse was commanded, not that door movement was proven. The core passes payload to this adapter during one call and never copies, logs or persists it. The transport receive buffer must be wiped after handling. Telephone identity may be contextual evidence only, never a sole main-door credential.

## Channel, provisioning and time

Requests require an authenticated **and confidential** local channel with a bound peer principal, such as mutually authenticated TLS using an ESP-IDF-compatible implementation. The boolean passed to the host core is a trusted transport assertion, never a packet bit. The authenticated peer ID is also an explicit input to challenge issuance and request handling; the core rejects a frame whose `principal_id` differs from that peer. The core additionally verifies the frame HMAC. The MAC is HMAC-SHA-256 over the exact 90-byte prefix under a per-principal 256-bit key selected by `key_id`. The production verifier must compare all 32 tag bytes in constant time. Keys are provisioned and rotated only through a protected indoor process; unknown and revoked IDs fail closed. Do not provision a shared fleet key. Key storage, transport selection, clock, RTC and rotation are integration work, not supplied by this skeleton.

The indoor controller issues a fresh unpredictable 128-bit challenge using a controller CSPRNG. It keeps one volatile challenge per allowed principal for at most 5000 ms of **indoor monotonic time**. The P4 has no trusted time role. A successfully authenticated request consumes its challenge before credential policy, including when policy denies. A new challenge replaces an unused one without resetting attempt limits. Controller reboot clears all outstanding challenges. No packet may authorize access until fresh challenge service, protected key storage, credential policy and independent cutoff have restarted successfully. An RTC or equivalent trusted validity source is still required for temporary credential dates; if unavailable, temporary grants deny.

## Request frame

All fields are bytes in network order; no C structure packing or variable-length parser. Exactly 122 bytes, no trailing data. Offsets are zero-based. This revised pre-freeze v1 layout rejects old 121-byte requests.

| Offset | Length | Field | Rule |
| ---: | ---: | --- | --- |
| 0 | 4 | magic | ASCII `ACR1` |
| 4 | 1 | version | `1` |
| 5 | 1 | action | `1` = request entry; never a relay command |
| 6 | 1 | resource ID | nonzero logical resource, `1`–`16`; indoor registry decides meaning |
| 7 | 1 | credential class | `1` convenience, `2` higher assurance |
| 8 | 1 | key ID | provisioned principal-specific key slot |
| 9 | 1 | flags | zero; reject unknown bits |
| 10 | 8 | principal ID | transport-bound provisioned identity |
| 18 | 16 | request ID | independent unpredictable value for audit correlation; not a replay substitute |
| 34 | 16 | indoor challenge | exact outstanding value |
| 50 | 8 | credential ID | pseudonymous indoor record ID; no PIN here |
| 58 | 32 | credential payload | sensitive; meaning belongs to confidential credential adapter |
| 90 | 32 | MAC | HMAC-SHA-256 over bytes 0–89 |

Resource IDs are generic bounded handles, not product names or actuator addresses. The authenticated value is resolved through protected indoor configuration to an actuator profile containing an indoor-only actuator ID, firmware pulse and independent cutoff maximum. Unknown IDs and failed lookups deny. This skeleton has one active actuator at a time and a resource ID ceiling of 16; neither defines a production resource registry.

The challenge response supplies the challenge only to an authenticated, confidential transport peer; no unlock result or credential value is included. A request ID must be nonzero and generated uniquely by the client, but the one-shot challenge is the authoritative replay guard. The controller can report bounded reason codes without logging payload, PIN, MAC, challenge, key or request frame. Rate limits apply to authenticated attempts per principal and survive P4 restart because state is indoors: at least one second between attempts and a 30-second lockout after three failed credential checks. Four concurrent principal slots are supported by this skeleton; no eviction when full. A stale signed frame is rejected after MAC verification without consuming or locking the current challenge, so an eavesdropper replay cannot invalidate the legitimate client's fresh challenge; the transport must separately bound replay traffic and CPU load. Production must also consider per-credential and global/network denial-of-service limits.

## Verification and actuator order

1. Confirm exact frame length, magic/version/action/class/flags, bounded nonzero resource ID, nonzero IDs and a trusted confidential channel.
2. Match provisioned principal and explicit authenticated transport identity, outstanding challenge state and indoor deadline.
3. Verify the full-frame MAC, match the challenge and consume it.
4. Enforce principal attempt limit and class eligibility. Reject a busy actuator, then resolve the authenticated resource through protected indoor policy. An unknown resource, lookup error or invalid profile denies before a potentially consuming credential check.
5. Verify the credential **for that resource**. On authorization, atomically consume any one-time grant before physical actuation. Arm the independent hardware cutoff using the validated indoor profile, then assert only its indoor actuator for its validated firmware pulse. This skeleton enforces provisional software safety ceilings of 1000 ms pulse and 1500 ms cutoff, with `0 < pulse < cutoff`; these are fail-closed bounds, **not production timings or a hardware selection**. The cutoff circuit must independently enforce the selected bound even if firmware stalls. On timeout or fault, force the cutoff safe before attempting relay-off; boot/fault adapters must force all outputs off. A failed cutoff arm or output operation latches fault. Outputs must be electrically de-energized before boot and on reset even if firmware never executes.

Malformed, unknown, expired, replayed, unauthenticated, unconfidential, disallowed and failed-policy requests never energize the relay. Tamper reports are event-only. Request-to-exit and door contacts belong to separate protected indoor inputs and are outside this network request protocol.

## Integration gates and remaining threats

- Select indoor MCU, secure key storage/provisioning/rotation and an authenticated confidential transport; bind transport peer to principal. The host MAC test key is not a deployable key.
- Implement a credential verifier with PIN hashing/keyed storage appropriate to the MCU, constant-time comparisons, durable temporary usage and revocation, trusted validity time, and secret buffer zeroization. The skeleton callback intentionally supplies no working PIN implementation.
- Design independent maximum-on cutoff and relay default-off circuitry; verify stuck firmware, reset, brownout, welded contact, actuator polarity, REX/egress/fire rules and door held/forced sensing on hardware before connection to a real strike.
- Define the protected indoor resource registry, credential-to-resource grants, actuator mapping and production timing profiles. Confirm each profile against actuator data and a separately reviewed hardware maximum-on bound; the host test's 250/500 ms values are illustrative skeleton values only.
- Prove controller RNG uniqueness and monotonic clock behavior. If the challenge, transport, key store, policy or cutoff is unavailable, deny. An attacker with P4 firmware control can still steal P4-entered PINs and submit attempts with its P4 key; constrain those credentials accordingly.
