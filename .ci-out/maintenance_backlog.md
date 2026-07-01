# Maintenance Backlog

Only non-blocking maintenance items remain.

## M1
- Item: `app/admin_ui.py` can later be split into `app/admin_static/admin.html`, `app/admin_static/admin.css`, and `app/admin_static/admin.js`.
- Status: accepted-maintenance.
- Constraint: do this only in a dedicated maintenance task with e2e and screenshot regression.

## M2
- Item: settings C-class `dev_mock` APIs can later connect to real configuration storage.
- Status: non-blocking.
- Constraint: keep `meta.dev_mock=true` until real persistence is implemented and verified.

## M3
- Item: if a Node frontend stack is introduced later, add `npx playwright test`.
- Status: non-blocking.
- Constraint: do not add Node dependencies only for the current Python-backed admin.
