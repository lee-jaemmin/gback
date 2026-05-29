# CODE_REVIEW.md

## Review checklist

### Correctness

- Does the change solve the requested issue?
- Are edge cases handled?
- Are null values handled safely?
- Are async states handled correctly?

### Flutter

- Is the widget tree readable?
- Are rebuilds reasonable?
- Is existing state management style preserved?
- Is formatting applied?

### Firebase

- Are reads/writes minimized?
- Are listeners disposed or scoped correctly?
- Could the query require a new index?
- Could this break existing production documents?

### Product risk

- Could this disrupt stores currently using the app?
- Does the change affect table status, reservation status, billing, auth, or store settings?
- Is manual QA clearly described?

### Avoid

- Large unrelated refactors
- New dependencies without justification
- Silent schema changes
- Unclear migration assumptions