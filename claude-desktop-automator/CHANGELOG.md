# Changelog

All notable changes to Claude Desktop Automator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-11-22

### Added
- Initial release of Claude Desktop Automator
- Core automation components:
  - `ClaudeDesktopController`: Window control and I/O management
  - `LimitDetector`: Rate limit detection using OCR
  - `SessionManager`: Session persistence and recovery
  - `Automator`: Main orchestration engine
- CLI interface with multiple modes:
  - Interactive mode for live chatting
  - Batch mode for processing prompt files
  - Single prompt mode for one-off queries
  - Statistics display
- Configuration system:
  - YAML-based configuration
  - Environment variable support
  - Customizable detection keywords
  - Adjustable retry and timing settings
- Session management features:
  - Automatic session saving
  - Context preservation
  - Recovery history tracking
  - Session export functionality
- Comprehensive logging:
  - File and console output
  - Log rotation and compression
  - Error screenshot capture
  - Debug mode support
- Rich CLI with:
  - Beautiful terminal output
  - Progress tracking
  - Statistics tables
  - Colored logs
- Documentation:
  - Detailed README with examples
  - API documentation in docstrings
  - Example scripts and prompts
  - Configuration templates
- Development tools:
  - Poetry configuration
  - Black/Flake8/MyPy setup
  - Test framework structure
  - Git ignore patterns

### Features
- ✅ Automated prompt sending via GUI automation
- ✅ OCR-based rate limit detection
- ✅ Automatic session recovery when limits hit
- ✅ Humanized typing delays
- ✅ Retry logic with exponential backoff
- ✅ Context preservation across recoveries
- ✅ Batch processing with progress tracking
- ✅ Interactive REPL mode
- ✅ Configurable base instructions
- ✅ Session statistics and analytics

### Known Limitations
- Windows only (pywinauto limitation)
- Requires Claude Desktop GUI to be visible
- OCR accuracy depends on screen resolution
- Response reading uses clipboard (may need enhancement)

### Dependencies
- Python 3.11+
- pyautogui 0.9.54+
- pywinauto 0.6.8+
- pytesseract 0.3.10+
- Pillow 10.1.0+
- pyyaml 6.0.1+
- python-dotenv 1.0.0+
- rich 13.7.0+
- loguru 0.7.2+
- pyperclip 1.8.2+

## [Unreleased]

### Planned Features
- [ ] macOS and Linux support
- [ ] Enhanced OCR-based response reading
- [ ] Visual element detection (loading indicators)
- [ ] Conversation branching
- [ ] Markdown/JSON export
- [ ] Web dashboard
- [ ] Docker support
- [ ] Unit tests
- [ ] Integration tests
- [ ] CI/CD pipeline

---

## Version History

- **0.1.0** - Initial release with core functionality
