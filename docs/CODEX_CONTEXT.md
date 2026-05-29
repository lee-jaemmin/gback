# CODEX_CONTEXT.md

## Product

This app is a real-time table management service for clubs/stores.
Store staff use it to manage table status, reservations, and operational flow.

## Business situation

- Solo founder project.
- Production users: 2-3 stores.
- Priority: stability, quick bug fixes, and practical feature shipping.
- Avoid big refactors unless they clearly reduce future bugs or are explicitly requested.

## Tech stack

- Flutter
- Firebase
  - Firestore
  - Firebase Auth
  - Firebase Storage / Functions if present in repo
- VS Code
- Codex CLI and Codex VS Code extension

## Engineering priorities

1. Do not break existing store operations.
2. Minimize Firestore read/write cost.
3. Keep UI responsive.
4. Keep changes small and reviewable.
5. Prefer incremental improvements over architecture rewrites.

## Common task types

- Fix runtime errors
- Fix Firestore data inconsistencies
- Add a page
- Add a feature to an existing page
- Improve UI flow
- Refactor only around touched code
- Investigate production-like bugs

## Risk areas

- Firestore document paths
- Firestore query indexes
- Auth-dependent logic
- Real-time listeners
- Table status synchronization
- Date/time handling
- Store-specific settings
- Payment/subscription logic if present