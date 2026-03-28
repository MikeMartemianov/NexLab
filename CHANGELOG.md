# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.9.1] - 2026-03-28
### Fixed
- **CLI Execution**: Fixed a `NameError` in `cli.py` where new command functions (`logs_cmd`, `version_cmd`, `gui_cmd`) were not properly defined.

## [0.9.0] - 2026-03-28
### Added
- **NexLab Logs**: New `nexlab logs` command.
- **NexLab GUI**: New `nexlab gui` command.
- **NexLab Version**: New `nexlab version` command.
- **Persistence Hooks**: Added `FileLogger`.

## [0.8.5] - 2026-03-28
### Fixed
- **Sanitization Refinement**: Preserving `/v1` in base URLs.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
