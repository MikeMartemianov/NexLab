# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.8.5] - 2026-03-28
### Fixed
- **Sanitization Refinement**: Fixed `_sanitize_base_url` to preserve `/v1` in base URLs. This is essential for OpenAI-compatible providers like Cerebras and Groq that require the version prefix.

## [0.8.4] - 2026-03-27
### Fixed
- **URL Auto-Sanitization**: Added automatic stripping of redundant suffixes.
- **Improved Error Guidance**: Added hints for 404 errors.

## [0.8.3] - 2026-03-27
### Fixed
- **Custom Provider Persistence**: Refactored the runtime pipeline to preserve `FullConfig` objects.
- **Base URL Flexibility**: Made `OpenAIProvider`'s API key check optional when using a custom `base_url`.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
