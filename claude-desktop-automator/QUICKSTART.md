# Quick Start Guide

Get up and running with Claude Desktop Automator in 5 minutes!

## Prerequisites Checklist

- [ ] Windows 10/11
- [ ] Python 3.11+ installed
- [ ] Claude Desktop app installed and running
- [ ] Tesseract OCR installed

## Step 1: Install Tesseract OCR (5 minutes)

1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer (use default path: `C:\Program Files\Tesseract-OCR`)
3. Verify installation:
   ```bash
   tesseract --version
   ```

## Step 2: Install Python Dependencies (2 minutes)

```bash
cd claude-desktop-automator
pip install -r requirements.txt
```

Or with Poetry:
```bash
poetry install
poetry shell
```

## Step 3: First Run (30 seconds)

### Try Interactive Mode

```bash
python -m claude_automator.cli interactive
```

This will:
1. Connect to Claude Desktop
2. Let you type prompts interactively
3. Handle rate limits automatically

**Example:**
```
> What is Python?
Claude: Python is a high-level programming language...

> Can you show a code example?
Claude: Certainly! Here's an example...

> exit
```

## Step 4: Try Batch Mode (1 minute)

Create a file `my_prompts.txt`:
```text
What is machine learning?
Explain neural networks in simple terms
What are the applications of AI?
```

Run batch processing:
```bash
python -m claude_automator.cli batch my_prompts.txt
```

## Configuration (Optional)

Edit `config/config.yaml` to customize:

```yaml
claude_desktop:
  input_delay_ms: 50        # Typing speed
  response_timeout_sec: 120 # Wait time

detection:
  use_ocr: true            # Enable rate limit detection
```

## Common Issues

### "Claude Desktop window not found"
→ Make sure Claude Desktop is running

### "TesseractNotFoundError"
→ Install Tesseract and add to PATH

### Prompts not sending
→ Increase `input_delay_ms` in config to 100-200

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Check `examples/` folder for code samples
- Customize `config/base_instructions.txt` for your use case

## Getting Help

1. Check the [Troubleshooting](README.md#troubleshooting) section
2. Review logs in `logs/automator.log`
3. Look at error screenshots in `logs/screenshots/`

---

**You're ready to automate! 🚀**

For detailed documentation, see [README.md](README.md)
