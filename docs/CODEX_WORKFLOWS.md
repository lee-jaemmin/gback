# CODEX_WORKFLOWS.md

## Bug fix workflow

1. Reproduce or infer the bug from the error message.
2. Locate the smallest relevant code path.
3. Explain the suspected cause.
4. Make the smallest safe fix.
5. Run `dart format .` and `flutter analyze`.
6. Summarize changed files, cause, fix, and remaining risk.

## Feature/page addition workflow

1. Find similar existing pages/features.
2. Reuse existing navigation, state management, theme, and Firebase patterns.
3. Create the minimum required UI and logic.
4. Avoid adding packages unless necessary.
5. Check empty, loading, error, and permission states.
6. Run formatting/analyze.
7. Provide manual QA steps.

## Firebase change workflow

1. Identify affected collections/documents.
2. Check existing read/write patterns.
3. Avoid additional reads in loops.
4. Mention if a new Firestore index may be needed.
5. Avoid schema changes unless explicitly requested.
6. If schema change is unavoidable, describe migration/backward compatibility.

## UI change workflow

1. Match existing design system and spacing.
2. Check small-screen behavior.
3. Preserve loading/error/empty states.
4. Avoid overengineering animations.
5. Provide manual test scenarios.