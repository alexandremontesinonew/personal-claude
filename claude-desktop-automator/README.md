# Claude Desktop Automator

> **Automated interaction system for Claude Desktop App with intelligent rate limit detection and automatic session recovery.**

A professional Python automation tool that enables seamless batch processing, continuous interaction, and intelligent recovery when working with Claude Desktop on Windows.

## Features

- **🤖 Full Automation**: Send prompts programmatically via GUI automation
- **🔍 Smart Detection**: Automatic detection of rate limits and message caps using OCR
- **🔄 Auto-Recovery**: Seamlessly starts new conversations and restores context when limits are hit
- **💾 Session Management**: Persistent session storage with automatic context preservation
- **📊 Rich CLI**: Beautiful command-line interface with progress tracking and statistics
- **⚙️ Highly Configurable**: YAML-based configuration for all aspects of automation
- **🛡️ Error Handling**: Robust retry logic and error screenshot capture
- **📝 Logging**: Comprehensive logging with rotation and compression

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Interactive Mode](#interactive-mode)
  - [Batch Mode](#batch-mode)
  - [Single Prompt](#single-prompt)
- [Architecture](#architecture)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Prerequisites

Before installing, ensure you have:

### 1. Python 3.11 or higher

```bash
python --version  # Should be 3.11+
```

Download from [python.org](https://www.python.org/downloads/) if needed.

### 2. Tesseract OCR

Tesseract is required for text detection and rate limit identification.

**Windows Installation:**

1. Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (recommended path: `C:\Program Files\Tesseract-OCR`)
3. Add Tesseract to your PATH:
   - Search for "Environment Variables" in Windows
   - Edit System PATH
   - Add: `C:\Program Files\Tesseract-OCR`

**Verify Installation:**

```bash
tesseract --version
```

### 3. Claude Desktop App

- Download and install from [claude.ai](https://claude.ai/download)
- Ensure the app is running before starting automation

## Installation

### Option 1: Using Poetry (Recommended)

```bash
# Clone or navigate to the project directory
cd claude-desktop-automator

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Option 2: Using pip

```bash
# Clone or navigate to the project directory
cd claude-desktop-automator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

### Basic Configuration

The main configuration file is `config/config.yaml`. Key settings:

```yaml
claude_desktop:
  window_title: "Claude"          # Window title to search for
  input_delay_ms: 50              # Typing speed (lower = faster)
  response_timeout_sec: 120       # Max wait time for responses

automation:
  base_instructions: "config/base_instructions.txt"  # Initial prompt
  max_retries: 3                  # Retry attempts on failure
  humanize_delays: true           # Add random variance to timing

detection:
  limit_keywords:                 # Keywords that indicate limits
    - "limit"
    - "rate limit"
    - "too many"
  use_ocr: true                   # Enable OCR-based detection

logging:
  level: "INFO"                   # DEBUG, INFO, WARNING, ERROR
  file: "logs/automator.log"
  screenshot_on_error: true       # Save screenshots on errors
```

### Base Instructions

Edit `config/base_instructions.txt` to set the initial prompt sent to Claude when starting new conversations:

```text
You are a helpful AI assistant. This is an automated session.

Please follow these guidelines:
- Provide clear and concise responses
- Maintain context across multiple messages
- Be thorough in your explanations
```

## Usage

### Interactive Mode

Chat with Claude interactively through the automation system:

```bash
# Using Poetry
poetry run claude-automator interactive

# Or if installed
claude-automator interactive

# Short form
claude-automator i
```

**Example Session:**

```
> Tell me about Python decorators

Claude: [Response about decorators]

> Can you show an example?

Claude: [Code example]

> exit
```

### Batch Mode

Process multiple prompts from a file:

```bash
# Create a prompts file
cat > my_prompts.txt << EOF
Explain quantum computing in simple terms
What are the main programming paradigms?
How does machine learning differ from traditional programming?
EOF

# Run batch processing
claude-automator batch my_prompts.txt

# With custom config
claude-automator batch my_prompts.txt -c custom_config.yaml

# Without progress bar
claude-automator batch my_prompts.txt --no-progress
```

### Single Prompt

Send a one-off prompt:

```bash
claude-automator send "Explain the difference between async and threading in Python"
```

### View Statistics

```bash
claude-automator stats
```

Shows:
- Session duration
- Messages sent/received
- Recovery attempts
- Rate limit detections

### Additional Options

```bash
# Enable verbose logging
claude-automator -v interactive

# Use custom config
claude-automator -c path/to/config.yaml interactive

# Hide banner
claude-automator --no-banner batch prompts.txt

# Get help
claude-automator --help
claude-automator batch --help
```

## Architecture

### Core Components

```
src/claude_automator/
├── core/
│   ├── controller.py      # Window control and input/output
│   ├── detector.py        # Rate limit and error detection
│   ├── session.py         # Session persistence and recovery
│   └── automator.py       # Main orchestrator
├── utils/
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging setup
│   └── helpers.py         # Utility functions
└── cli.py                 # Command-line interface
```

### How It Works

1. **Initialization**
   - Connects to Claude Desktop window using `pywinauto`
   - Loads base instructions from config
   - Initializes session tracking

2. **Prompt Processing**
   - Sends text via clipboard or simulated typing
   - Waits for response completion
   - Reads response via clipboard or OCR

3. **Limit Detection**
   - Continuously monitors for rate limit indicators
   - Uses OCR to read on-screen text
   - Checks for specific keywords and patterns

4. **Auto-Recovery**
   - Saves current context to disk
   - Opens new conversation (Ctrl+N)
   - Restores base instructions
   - Continues from where it stopped

5. **Session Management**
   - Auto-saves session every 60 seconds
   - Stores prompts and responses
   - Tracks recovery history
   - Enables session restoration

## Development

### Project Structure

```
claude-desktop-automator/
├── src/
│   └── claude_automator/       # Source code
├── config/                     # Configuration files
├── tests/                      # Unit tests (TODO)
├── logs/                       # Log files and screenshots
├── pyproject.toml             # Poetry configuration
├── requirements.txt           # Pip requirements
└── README.md                  # This file
```

### Running Tests

```bash
# Install dev dependencies
poetry install --with dev

# Run tests (when implemented)
poetry run pytest

# With coverage
poetry run pytest --cov=claude_automator
```

### Code Style

```bash
# Format code
poetry run black src/

# Lint
poetry run flake8 src/

# Type checking
poetry run mypy src/
```

### Adding Features

1. Modify core classes in `src/claude_automator/core/`
2. Update configuration schema in `config/config.yaml`
3. Add CLI commands in `src/claude_automator/cli.py`
4. Update this README

## Troubleshooting

### Claude Desktop Not Found

**Error:** `Claude Desktop window not found`

**Solutions:**
- Ensure Claude Desktop is running
- Check window title in config matches actual window title
- Try running Claude Desktop as administrator

### Tesseract Not Found

**Error:** `TesseractNotFoundError`

**Solutions:**
- Install Tesseract (see [Prerequisites](#prerequisites))
- Add Tesseract to system PATH
- Verify with `tesseract --version`

### Rate Limit Not Detected

**Symptoms:** Automation doesn't recover when limit is hit

**Solutions:**
- Enable OCR: Set `detection.use_ocr: true` in config
- Add language: Set `detection.ocr_lang: "eng+por"` (or your language)
- Adjust keywords: Add custom limit messages to `detection.limit_keywords`
- Check screenshots in `logs/screenshots/` to see what OCR is reading

### Prompts Not Sending

**Symptoms:** Text doesn't appear in Claude Desktop

**Solutions:**
- Increase `input_delay_ms` in config (try 100-200ms)
- Enable clipboard mode (default)
- Ensure Claude Desktop window is in focus
- Check logs in `logs/automator.log`

### Response Reading Fails

**Symptoms:** Empty responses or errors

**Solutions:**
- The current implementation uses clipboard for reading
- Claude Desktop's UI might not support text selection
- Consider using OCR-based reading (requires implementation enhancement)
- Check error screenshots in `logs/screenshots/`

### Performance Issues

**Symptoms:** Slow execution

**Solutions:**
- Disable OCR if not needed: `detection.use_ocr: false`
- Reduce `response_timeout_sec`
- Decrease `input_delay_ms` (if typing is reliable)
- Use batch mode instead of interactive

## Advanced Usage

### Custom Recovery Logic

Extend the `Automator` class to add custom recovery behavior:

```python
from claude_automator import Automator

class CustomAutomator(Automator):
    def _attempt_recovery(self) -> bool:
        # Custom recovery logic
        self.send_notification("Recovering...")
        return super()._attempt_recovery()
```

### Programmatic Usage

Use the library in your own Python scripts:

```python
from claude_automator import Automator

# Create automator
automator = Automator()

# Initialize
if automator.initialize():
    # Send prompts
    response = automator.send_with_retry("Hello Claude!")
    print(response)

    # Get stats
    stats = automator.get_stats()
    print(f"Messages sent: {stats['prompts_sent']}")

    # Cleanup
    automator.stop()
```

### Context Manager

```python
from claude_automator import Automator

with Automator() as automator:
    response = automator.send_with_retry("Explain async/await")
    print(response)
# Automatically saves and cleans up
```

## Limitations

- **Windows Only**: Currently only supports Windows (pywinauto limitation)
- **GUI Dependent**: Requires Claude Desktop to be visible and responsive
- **OCR Accuracy**: Text detection depends on screen resolution and font clarity
- **Rate Limits**: Subject to Claude Desktop's actual rate limiting policies

## Future Enhancements

- [ ] macOS and Linux support
- [ ] Better response reading (OCR-based)
- [ ] Visual element detection (loading spinners, etc.)
- [ ] Conversation branching and management
- [ ] Export conversations to markdown/JSON
- [ ] Web dashboard for monitoring
- [ ] Docker support

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for educational and automation purposes.

## Disclaimer

This tool automates interaction with Claude Desktop using GUI automation. Use responsibly and in accordance with Anthropic's terms of service. The authors are not responsible for any violations or issues arising from use of this tool.

---

**Made with ❤️ for Claude Desktop power users**

For issues and feature requests, please open an issue on GitHub.
