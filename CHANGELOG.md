# Changelog

All notable changes to the `smart-agent-arch` project will be documented in this file.

## [0.8.0] - 2026-03-27
### Added
- **Self-Update System**: New `update_from_github()` tool to safely pull latest changes.
- **Improved Documentation**: Added configuration examples for all 17 customization dimensions.

## [0.7.0] - 2026-03-27
### Added
- **Dynamic Tool Creation System**: Automatically discover and register tools from `utils/custom_tools/`.
- `ToolsLoader` component for metadata extraction from Python functions (docstrings, type hints).
- `@export_tool` decorator for explicit tool opting-in.
- Automatic generation of command patterns and argument descriptions for the AI.

### Changed
- Updated `UserAIFacade` to include automatic tool refreshing on startup.
- Synchronized versioning across `pyproject.toml` and `version.py`.

## [0.6.1] - 2026-03-27
### Fixed
- Improved root directory resolution for local development and bundled builds.
- Cleaned up Git repository with a comprehensive root `.gitignore`.

## [0.1.0] - 2026-03-18
### Added
- Initial release of `smart-agent-arch`.
- Basic `UserAIFacade` with Ollama/OpenAI support.
- Core components: Mentor AI, Deep Thinker, Fast Memory.
- Static command parser for manual tool definitions.
