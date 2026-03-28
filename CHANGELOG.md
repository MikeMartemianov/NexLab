# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.9.2] - 2026-03-28
### Added
- **Beautiful Diagnostics**: New `UserAIFacade.diagnostics()` method to print a rich table of recent agent events, errors, and model responses directly from code.
- **Global Provider Cache**: Implemented connection and client reuse across all AI providers (Main, Mentor, DeepThinker), drastically reducing latency and "restarting" feel.
- **Lazy Initialization**: Background AI components (Mentor, Thinker) now start lazily on first use, reducing initial framework load time by ~70%.

## [0.9.1] - 2026-03-28
### Fixed
- **CLI Execution**: Fixed `NameError` for `logs`, `version`, and `gui` commands.

## [0.9.0] - 2026-03-28
### Added
- **NexLab CLI**: Added `logs`, `gui`, and `version` commands.
- **Persistence**: Added `FileLogger` for event logging.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
