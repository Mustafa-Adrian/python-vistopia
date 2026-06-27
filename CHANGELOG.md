# Changelog

## 0.2.0 - 2026-06-27

### Added

- Added `save-show --id-list` for downloading or processing multiple show IDs, with range syntax such as `1-3,8,10`.
- Added `save-show --skip-existing` to skip existing non-empty `.mp3` files when resuming an interrupted download.
- Added `save-show --skip-first` to skip the first N matched episodes.
- Added `save-show --playlist-only` to generate playlist/catalog files without downloading or tagging audio.
- Added automatic `playlist.m3u8` generation for player-friendly ordered playback.
- Added automatic `catalog.tsv` generation with `index`, `title`, `api_sort_number`, and `filename` columns.
- Added show-level and episode-level CLI progress logs so interrupted runs can be diagnosed from the last printed line.

### Changed

- `save-show --id` is now optional at Click parsing time so it can be used mutually exclusively with `--id-list`; one of them is still required.
- `save-show --episode-id` is now rejected when used with `--id-list`, because episode numbers are scoped to a single show.
- Audio downloads now write to a `.mp3.part` temporary file first and rename to `.mp3` only after a successful download.
- `save-show --playlist-only` avoids fetching show metadata that is only needed for audio tagging.

### Notes

- `api_sort_number` may skip numbers because it comes from the upstream API. Use the generated `index` column or `playlist.m3u8` for local playback order.
