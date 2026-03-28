# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.9.0] - 2026-03-28
### Added
- **NexLab Logs**: New `nexlab logs` command to view persistent agent events.
- **NexLab GUI**: New `nexlab gui` command to launch the native desktop application.
- **NexLab Version**: New `nexlab version` command for quick version checks.
- **Persistence Hooks**: Added `FileLogger` to save agent lifecycle events to a JSON-line log file.

## [0.8.5] - 2026-03-28
### Fixed
- **Sanitization Refinement**: Preserving `/v1` in base URLs to maintain compatibility with Cerebras/Groq.

## [0.8.4] - 2026-03-27
### Fixed
- **URL Auto-Sanitization**: Automatic stripping of redundant endpoints.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
