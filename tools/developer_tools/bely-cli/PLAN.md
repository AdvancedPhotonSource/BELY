# Fix attachment image preview race

## Context

Rapid attachment/file preview changes can leave the previous image widget mounted while a new image preview callback mounts another widget with the same fixed ID. Textual then raises `DuplicateIds` for `attachment-image` (and the local-file preview has the same asynchronous removal pattern). SSH/terminal image rendering can expose this timing race even when local rendering does not, because the current code starts deferred removal but mounts the replacement without waiting for removal to finish.

## Approach

First reproduce the reported failure deterministically in a Textual test by mounting an initial fixed-ID image widget, initiating the existing deferred removal path, and immediately running the next image callback. Confirm the test fails with `DuplicateIds` before changing production code.

Then move image-container replacement into each async UI callback: await `remove_children()`, re-check the existing preview token after that await, and only then mount the current image. This serializes Textual’s deferred removal with mounting, prevents duplicate fixed IDs, and prevents a callback that became stale while awaiting removal from displaying old content. Apply the same lifecycle handling to remote attachment previews and local upload-file previews; retain selection-time clearing for text/metadata previews.

## Files to modify

- `src/bely_cli/tui/screens/attachments.py` — coordinate asynchronous image-widget replacement.
- `test/test_tui_screens.py` — add regression coverage for repeated/racing image previews (exact test location to confirm).

## Reuse

- Existing `_preview_token` guards in both `AttachmentScreen` and `AttachmentFileScreen`.
- Existing preview methods and Textual test-app patterns in `test/test_tui_screens.py`.

## Steps

- [x] **Milestone 1 — reproducer only:** Add and run a focused Textual regression test against unchanged production code to demonstrate the reported `DuplicateIds` failure. Pause and hand control back for review; do not implement the fix yet.
- [x] **Milestone 2 — minimal fix:** After user approval, update `_show_image()` to await removal of any existing media child, revalidate the token, and mount exactly one image widget. Keep selection-time clearing so text/metadata selections promptly remove prior images. Re-run the reproducer and pause for review.
- [x] **Milestone 3 — parallel path and edge case:** After user approval, apply equivalent handling and regression coverage to `_show_local_image()`, and add a stale-token assertion so an outdated callback cannot mount after replacement awaits. Run focused tests and pause for review.
- [x] **Milestone 4 — broader verification:** After user approval, run the requested broader test suite and report results for final review.
- [x] Update user-facing documentation only if behavior/surface changes (none expected).

## Verification

- Record the focused reproducer failing before the fix and pause for review.
- After approval and implementation, record the same reproducer passing and pause again.
- Run focused attachment/TUI screen tests.
- Run the full test suite via `uv run pytest -n auto test` (or `./run_test.sh`).
- Manually move rapidly between image and non-image attachments/local files and confirm no traceback or stale image appears.
