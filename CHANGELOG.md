# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.8.2] - 2026-03-27
### Added
- **Event Hook System**: Lifecycle hooks (`on_input`, `on_tool_end`, etc.) for developer extensibility.
- **Diagnostic CLI**: Added `nexlab doctor` and `nexlab status` with beautiful `rich` output.
- **Diagnostic Mode**: New `detailed_diagnostics` configuration flag.
- **Improved Aesthetics**: Full integration of the `rich` library for terminal interactions.

### Removed
- Redundant `sample_tools.py` in favor of professional diagnostics.

## [0.8.1] - 2026-03-27
### Added
- **NexLab CLI**: Introduced the `nexlab` command-line utility.
- **Self-Update**: `nexlab update` command for GitHub synchronization.

## [0.8.0] - 2026-03-27
### Added
- **Dynamic Tool Creation**: Automatic discovery and registration of tools.
- **Introspection Engine**: Metadata extraction from docstrings and type hints.
- **Advanced Documentation**: Initial expansion to 18 customization dimensions.

## [0.6.1] - 2026-03-27
### Fixed
- Improved root directory resolution and workspace sanitation.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
