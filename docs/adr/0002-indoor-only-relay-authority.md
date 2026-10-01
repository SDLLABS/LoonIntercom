# ADR-0002: Physical unlock authority stays indoors

Status: accepted for architecture v2, 2026-10-01.

## Context

The outdoor panel can be removed or shorted. OpenChime's proposed Ring hardware places strike/gate relay control at that panel. SDLLABS requires a stronger physical trust boundary.

## Decision

Place all strike/gate switching, actuator power paths, credential policy, request verification, replay state and maximum-on cutoff on a protected indoor controller. P4 may collect input and send an authenticated, short-lived access request naming a bounded logical resource; protected indoor policy maps that resource to an actuator profile and verifies credential scope. P4 cannot supply a GPIO, relay state, pulse or cutoff duration or directly energize outputs. No outdoor wire pair may unlock by shorting. HA, MQTT and NVR have no direct relay interface. Indoor request-to-exit and door-contact inputs are separately wired to the controller. Tamper never triggers unlock.

The indoor verifier must reject unauthenticated, malformed, stale or replayed requests, apply rate limits and credential policy, and keep relays de-energized at boot, reset and fault. Protected indoor configuration supplies resource-specific timing within hard software safety bounds; a firmware timer plus an independent maximum-on mechanism bound pulse length. PINs are not stored or logged in plaintext; temporary credentials have bounded time/uses, resource scope and revocation. Caller ID alone cannot authorize a main entrance.

Indoor verification protects relay authority, but a keypad attached to the physically untrusted P4 lets a compromised P4 observe PIN entry. Two assurance models remain open: a P4-connected keypad for convenience credentials with bounded scope and revocation, or a dedicated secure keypad/controller communicating directly with the indoor access controller for higher-assurance credentials. Encryption from P4 to indoors cannot conceal a PIN already observed by P4. This ADR does not select keypad hardware.

## Consequences

WP4 must specify principal identity, key provisioning/rotation, authentication, freshness, reboot behavior and credential classes for each keypad assurance model before coding. Physical P4 compromise remains able to submit attempts as its own principal and read PINs entered through it; indoor lockout, credential scope and revocation limit that risk. Controller loss means no remote unlock. Exact fail-secure/egress behavior, actuator polarity, cutoff circuit, and local code requirements need hardware review before installation.

## Rejected alternatives

Outdoor relay GPIO, a generic `unlock` MQTT topic, or HA automation directly operating a relay would cross the physical boundary and are prohibited.
