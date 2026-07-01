# Release Notes

## Single-User Owner Admin
- The backend is now organized around one Owner user, not a multi-tenant or role-matrix product.
- The primary admin experience is available from `/` and `/admin`.

## Overview
- The overview presents generation, pending handling, export status, platform risk, pending issues, recent failures, and QA entry points.

## Processing Center
- Processing-center cancel and requeue actions now call real admin APIs.
- State is persisted and remains after refresh.

## Failure Center
- Failure tasks show stage, reason, status, and available actions.
- Cancel and requeue are persisted through the admin service layer.

## Generation Workbench
- Theme-based prompt generation is available.
- Local prompt optimization and remote-failure fallback are recorded.
- Prompt history is persisted and survives refresh.

## Sticker Library Auto-Filtering
- Sticker library filters auto-apply without a manual submit step.
- Rows are loaded through the unified sticker adapter.
- Thumbnails use real `/admin-assets/...png` media paths.

## QA Review
- QA rejection requires a reason before recording the rejection action.
- QA paths remain covered by the formal e2e smoke flow.

## Export Delivery
- Export delivery supports pagination, row export, and batch export.
- Batch and row export actions update persisted export task state.

## System Settings
- Platform rules and generation source configuration pages are reachable from system settings.
- Settings APIs remain explicitly marked `dev_mock=true` until real configuration storage is added.

## Theme Switching
- The top-bar theme switcher supports multiple themes.
- Theme choice persists after refresh through browser local storage.

## Persistence
- Admin issue, failure, export, and prompt-history state is persisted through `data/admin_state.json`.
- Persistence is accessed through `app/admin_store.py` and `app/admin_services.py`, not route-local mutable mock state.

## Tests And Screenshot Evidence
- Python compile check passed.
- `pytest -q`: 6 passed.
- `pytest -q tests/e2e/test_admin_ui_playwright.py`: 1 passed.
- Final screenshot evidence is under `.ci-out/screenshots-loop4/`.
