# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.8.3] - 2026-03-27
### Fixed
- **Custom Provider Persistence**: Refactored the runtime pipeline to preserve `FullConfig` objects, preventing the loss of custom provider function pointers.
- **Base URL Flexibility**: Made `OpenAIProvider`'s API key check optional when using a custom `base_url` (e.g., for local LLM servers).
- **Provider Resolution**: Updated `ModelResolver` to explicitly handle `custom_function` and `custom` provider modes.

## [0.8.2] - 2026-03-27
### Added
- **Event Hook System**: Lifecycle hooks (`on_input`, `on_tool_end`, etc.) for developer extensibility.
- **Diagnostic CLI**: Added `nexlab doctor` and `nexlab status` with beautiful `rich` output.
- **Diagnostic Mode**: New `detailed_diagnostics` configuration flag.

## [0.8.1] - 2026-03-27
### Added
- **NexLab CLI**: Introduced the `nexlab` command-line utility.
- **Self-Update**: `nexlab update` command for GitHub synchronization.

## [0.8.0] - 2026-03-27
### Added
- **Dynamic Tool Creation**: Automatic discovery and registration of tools.
- **Introspection Engine**: Metadata extraction from docstrings and type hints.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
