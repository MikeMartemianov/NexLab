# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.8.4] - 2026-03-27
### Fixed
- **URL Auto-Sanitization**: Added `_sanitize_base_url` to automatically strip redundant suffixes (`/v1`, `/chat/completions`, `/api/chat`) from `base_url`. This prevents 404 errors caused by double-appended endpoints.
- **Improved Error Guidance**: The `LiveRuntimeGateway` now provides specific hints for 404 errors, suggesting the correct provider for OpenAI-compatible services like Cerebras, Groq, or LocalAI.

## [0.8.3] - 2026-03-27
### Fixed
- **Custom Provider Persistence**: Refactored the runtime pipeline to preserve `FullConfig` objects.
- **Base URL Flexibility**: Made `OpenAIProvider`'s API key check optional when using a custom `base_url`.

## [0.8.2] - 2026-03-27
### Added
- **Event Hook System**: Lifecycle hooks (`on_input`, `on_tool_end`, etc.).
- **Diagnostic CLI**: Added `nexlab doctor` and `nexlab status`.

## [0.8.1] - 2026-03-27
### Added
- **NexLab CLI**: Introduced the `nexlab` command-line utility.
- **Self-Update**: `nexlab update` command.

## [0.8.0] - 2026-03-27
### Added
- **Dynamic Tool Creation**: Automatic discovery and registration of tools.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
