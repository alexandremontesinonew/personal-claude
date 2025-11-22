# Architecture Documentation

## Overview

Claude Desktop Automator is built with a modular architecture that separates concerns into distinct components. This document explains the internal structure and design decisions.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CLI Interface                        │
│                  (cli.py)                               │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                  Automator (Orchestrator)                │
│  - Initialization                                        │
│  - Prompt processing loop                                │
│  - Recovery coordination                                 │
│  - Statistics collection                                 │
└──┬───────────────┬───────────────────┬──────────────────┘
   │               │                   │
   ▼               ▼                   ▼
┌─────────┐  ┌──────────┐      ┌──────────────┐
│Controller│  │ Detector │      │SessionManager│
│         │  │          │      │              │
│-Window  │  │-OCR      │      │-Context Save │
│-Input   │  │-Keywords │      │-Recovery     │
│-Output  │  │-Errors   │      │-History      │
└────┬────┘  └─────┬────┘      └──────┬───────┘
     │             │                  │
     │             │                  │
     ▼             ▼                  ▼
┌────────────────────────────────────────────┐
│           Utility Layer                     │
│  - Config      - Logger      - Helpers     │
└────────────────────────────────────────────┘
```

## Core Components

### 1. Automator (`core/automator.py`)

**Purpose**: Main orchestrator that coordinates all components.

**Responsibilities**:
- Initialize all subsystems
- Manage automation lifecycle
- Coordinate prompt sending and response reading
- Handle error recovery
- Collect and report statistics

**Key Methods**:
- `initialize()`: Setup window connection and load base instructions
- `run()`: Main automation loop for batch processing
- `send_with_retry()`: Send prompts with automatic retry logic
- `_attempt_recovery()`: Coordinate recovery when limits are hit
- `send_interactive()`: REPL mode for manual interaction

**Design Pattern**: Facade pattern - provides simplified interface to complex subsystems.

### 2. ClaudeDesktopController (`core/controller.py`)

**Purpose**: Direct interaction with Claude Desktop window.

**Responsibilities**:
- Window detection and focus management
- Sending prompts (keyboard/clipboard)
- Reading responses
- Starting new conversations

**Technologies Used**:
- `pywinauto`: Windows automation framework
- `pyautogui`: Cross-platform GUI automation
- `pyperclip`: Clipboard management

**Key Methods**:
- `find_window()`: Locate Claude Desktop by title/class
- `send_prompt()`: Type or paste text into input field
- `read_response()`: Extract response text (clipboard-based)
- `start_new_chat()`: Trigger new conversation (Ctrl+N)
- `wait_for_response_complete()`: Poll until response finishes

**Challenges**:
- Window may lose focus
- Clipboard operations can be unreliable
- Response reading requires app-specific knowledge

**Future Improvements**:
- OCR-based response reading
- UI element detection for more reliable state checking
- Support for minimized windows

### 3. LimitDetector (`core/detector.py`)

**Purpose**: Detect when rate limits or message caps are reached.

**Responsibilities**:
- OCR text extraction
- Keyword matching for limit indicators
- Error message detection
- "Busy" state detection (Claude is typing)

**Technologies Used**:
- `pytesseract`: Python wrapper for Tesseract OCR
- `PIL/Pillow`: Image processing

**Detection Strategy**:
1. Take screenshot of window or region
2. Extract text using OCR
3. Search for configured keywords
4. Classify limit type (rate limit vs message limit)

**Key Methods**:
- `check_limit_reached()`: Main detection method
- `_extract_text_from_image()`: OCR processing
- `_check_text_for_limit()`: Keyword matching
- `get_limit_type()`: Classify detected limit

**Configuration**:
```yaml
detection:
  limit_keywords:
    - "limit"
    - "rate limit"
    - "too many"
  use_ocr: true
  ocr_lang: "eng+por"
```

**Accuracy Factors**:
- Screen resolution (higher is better)
- Font rendering quality
- OCR language packs installed
- Keyword list completeness

### 4. SessionManager (`core/session.py`)

**Purpose**: Persist session state and enable recovery.

**Responsibilities**:
- Track prompts and responses
- Save context to disk
- Load previous sessions
- Record recovery attempts
- Export conversation history

**Data Structure**:
```python
{
    "session_id": "session_20241122_143022",
    "start_time": "2024-11-22T14:30:22",
    "base_instructions": "...",
    "prompts": [
        {"timestamp": "...", "text": "...", "metadata": {}}
    ],
    "responses": [
        {"timestamp": "...", "text": "...", "metadata": {}}
    ],
    "recoveries": 3,
    "total_messages": 25,
    "recovery_history": [
        {"timestamp": "...", "reason": "rate_limit", "success": true}
    ]
}
```

**Key Methods**:
- `save_context()`: Persist session to JSON file
- `load_context()`: Restore session from disk
- `add_prompt()`/`add_response()`: Track conversation
- `record_recovery()`: Log recovery attempts
- `get_conversation_history()`: Retrieve message history
- `recover_session()`: Start new session with preserved context

**Auto-Save Strategy**:
- Saves every N seconds (configurable)
- Force save on recovery
- Save on shutdown
- Incremental saves to prevent data loss

### 5. Configuration System (`utils/config.py`)

**Purpose**: Centralized configuration management.

**Features**:
- YAML file parsing
- Environment variable support
- Dot-notation access (`config.get("claude_desktop.window_title")`)
- Path resolution (relative to project root)
- Type-safe property accessors

**Configuration Sections**:
- `claude_desktop`: Window and timing settings
- `automation`: Retry and delay configuration
- `detection`: OCR and keyword settings
- `recovery`: New chat and recovery settings
- `logging`: Log levels and output
- `session`: Auto-save configuration

### 6. Logging System (`utils/logger.py`)

**Purpose**: Comprehensive logging infrastructure.

**Technologies Used**:
- `loguru`: Modern Python logging library

**Features**:
- Dual output (console + file)
- Log rotation by size
- Compression of old logs
- Colored console output
- Contextual logging (file:function:line)

**Log Levels**:
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Potential issues
- ERROR: Errors with recovery
- CRITICAL: Fatal errors

### 7. Utility Helpers (`utils/helpers.py`)

**Purpose**: Reusable utility functions.

**Functions**:
- `humanized_delay()`: Random delays to appear human-like
- `take_screenshot()`: Capture screen or region
- `save_error_screenshot()`: Auto-save on errors
- `type_text()`: Simulate typing with delays
- `click_at_position()`: Humanized mouse clicks
- `press_hotkey()`: Keyboard shortcuts

**Design Philosophy**:
- Pure functions where possible
- No side effects except I/O
- Well-documented parameters
- Error handling with logging

## Data Flow

### Sending a Prompt

```
User Input
    │
    ▼
CLI parses command
    │
    ▼
Automator.send_with_retry()
    │
    ├─► SessionManager.add_prompt()
    │   └─► Save to session.json
    │
    ├─► Controller.send_prompt()
    │   ├─► Focus window
    │   ├─► Paste/type text
    │   └─► Press Enter
    │
    ├─► Controller.wait_for_response_complete()
    │   └─► Poll for completion
    │
    ├─► Controller.read_response()
    │   └─► Copy from clipboard
    │
    ├─► Detector.check_limit_reached()
    │   ├─► Take screenshot
    │   ├─► OCR extraction
    │   └─► Keyword matching
    │
    └─► SessionManager.add_response()
        └─► Save to session.json
```

### Recovery Flow

```
Limit Detected
    │
    ▼
Automator._attempt_recovery()
    │
    ├─► SessionManager.save_context(force=True)
    │   └─► Save current state
    │
    ├─► Controller.start_new_chat()
    │   ├─► Press Ctrl+N
    │   └─► Wait for new chat
    │
    ├─► Get base instructions
    │   └─► SessionManager.get_base_instructions()
    │
    ├─► Resend base instructions
    │   └─► Controller.send_prompt()
    │
    ├─► Wait for acknowledgment
    │   └─► Controller.wait_for_response_complete()
    │
    ├─► Record recovery
    │   └─► SessionManager.record_recovery()
    │
    └─► Continue automation
        └─► Return to main loop
```

## Design Patterns Used

1. **Facade Pattern** (Automator)
   - Simplifies complex subsystem interactions
   - Single entry point for automation

2. **Strategy Pattern** (Input methods)
   - Clipboard vs typing strategies
   - Switchable at runtime

3. **Observer Pattern** (Logging)
   - Multiple log handlers
   - Event-driven logging

4. **Template Method** (CLI commands)
   - Common initialization
   - Specialized execution

5. **Singleton Pattern** (Logger)
   - Single logger instance
   - Global configuration

## Error Handling Strategy

### Levels of Error Handling

1. **Retry Layer** (Automator)
   - Automatic retry with exponential backoff
   - Configurable max retries
   - Graceful degradation

2. **Recovery Layer** (Automator)
   - Session context preservation
   - Automatic chat restart
   - Context restoration

3. **Logging Layer** (All components)
   - Error screenshots
   - Stack traces
   - Contextual information

4. **User Feedback Layer** (CLI)
   - Rich error messages
   - Actionable suggestions
   - Progress indication

## Performance Considerations

### Optimization Strategies

1. **Screenshot Caching**
   - Avoid redundant captures
   - Region-based screenshots

2. **OCR Optimization**
   - Limit OCR to necessary regions
   - Configurable OCR intervals
   - Optional OCR disable

3. **Session Auto-Save**
   - Periodic saves instead of per-message
   - Async I/O (future improvement)

4. **Delay Tuning**
   - Configurable delays
   - Humanization vs speed trade-off

### Bottlenecks

1. **OCR Processing**: 100-500ms per screenshot
2. **Window Focus**: 200-500ms
3. **Response Waiting**: Variable (0-120s)
4. **Clipboard Operations**: 50-200ms

## Security Considerations

1. **Credentials**
   - No hardcoded secrets
   - Environment variable support
   - .env file ignored in git

2. **Screenshots**
   - May contain sensitive data
   - Stored locally only
   - Configurable auto-cleanup (future)

3. **Session Files**
   - Contains conversation history
   - Stored in local logs directory
   - Should be excluded from version control

## Testing Strategy

### Unit Tests
- Pure function testing
- Mock external dependencies
- Configuration validation

### Integration Tests
- Component interaction
- End-to-end flows
- Error scenarios

### Manual Testing
- Real Claude Desktop interaction
- Visual verification
- Performance benchmarks

## Future Architecture Improvements

1. **Plugin System**
   - Custom detectors
   - Alternative input methods
   - Export formats

2. **Async I/O**
   - Non-blocking operations
   - Parallel processing
   - Better responsiveness

3. **Web API**
   - REST endpoints
   - Remote control
   - Dashboard integration

4. **Database Backend**
   - Replace JSON files
   - Query capabilities
   - Better concurrency

5. **Event System**
   - Pub/sub architecture
   - Extensible hooks
   - Real-time monitoring

---

**Last Updated**: 2024-11-22
**Version**: 0.1.0
