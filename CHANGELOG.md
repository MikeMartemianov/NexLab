# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.9.3] - 2026-03-28
### Fixed
- **CLI Robustness**: Fixed an `AttributeError` in the `nexlab update` command. The error occurred when trying to decode string output from subprocess, which is no longer necessary as `text=True` is used.

## [0.9.2] - 2026-03-28
### Added
- **Beautiful Diagnostics**: New `UserAIFacade.diagnostics()` method.
- **Global Provider Cache**: Performance optimization.
- **Lazy Initialization**: Performance optimization.

## [0.9.1] - 2026-03-28
### Fixed
- **CLI Execution**: Fixed `NameError` for commands.

## [0.1.0] - 2026-03-18
### Added
- Initial release.
