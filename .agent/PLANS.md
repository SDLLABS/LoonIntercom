# Execution Plans for Codex

Use an execution plan for work that spans multiple components, changes architecture, introduces a protocol, or is expected to take more than one focused coding pass.

Store active plans under `.agent/plans/<short-name>.md`.

Every plan must contain:

## Goal

One concise paragraph describing the user-visible or system-level result.

## Non-goals

Explicitly state what will not be changed.

## Constraints

List applicable invariants from `/AGENTS.md`.

## Current state

What exists now, with concrete file paths and relevant upstream references.

## Proposed design

Interfaces, ownership boundaries, data flow and failure behaviour.

## Security analysis

For access-control, network-facing, update or credential work:
- trust boundaries;
- authentication;
- replay resistance;
- input validation;
- secret storage;
- failure mode;
- physical attack assumptions.

## Work breakdown

Small ordered steps. Each step should be independently reviewable when practical.

## Validation

Exact commands/tests to run and hardware checks that remain manual.

## Progress

A checklist updated during work.

## Decisions / discoveries

Record facts learned during implementation that change the plan.

## Final result

Summarise implementation, tests, limitations and follow-ups.

Do not silently expand scope. If a planned architectural assumption is false, update the plan before broadening the implementation.
