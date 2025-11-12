# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Chainlit-based chat interface** for interacting with local Ollama LLM models. The application provides a web UI for chatting with local AI models with complete privacy and no cloud dependency.

## Development Commands

### Running the Application
```bash
# Start with watch mode (auto-reload on changes)
uv run chainlit run main.py -w

# Start without watch mode
uv run chainlit run main.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_ollama_service.py -v

# Run tests matching a pattern
uv run pytest -k "test_pull" -v

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing
```

### Code Quality
```bash
# Lint with auto-fix
ruff check src/ tests/ --fix

# Format code
ruff format src/ tests/

# Type checking
mypy src/
```

### Dependency Management
```bash
# Sync dependencies (including dev extras)
uv sync --all-extras

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>
```

## Architecture Overview

### Core Design Patterns

1. **Service Layer Pattern**: Business logic is separated from UI handlers
   - `src/services/` contains all backend logic
   - `src/ui/` contains Chainlit decorators and UI handlers
   - Services are stateless and can be tested independently

2. **Chainlit Session Management**: User state is managed via `cl.user_session`
   - Each user has isolated session state (model, parameters, messages, system_prompt)
   - Session state persists across page refreshes but not browser restarts
   - Settings sidebar syncs with session state on initialization

3. **Pydantic Validation**: All data structures use Pydantic models for runtime type safety
   - `ModelParameters` validates temperature (0-2), top_p (0-1), max_tokens (≥1 or None)
   - Validation errors surface immediately rather than causing silent failures

4. **Async-First**: All I/O operations use async/await
   - Ollama SDK is synchronous, so blocking operations run in thread pool via `asyncio.to_thread()`
   - Streaming responses use async generators

### Critical Implementation Details

#### Ollama SDK Behavior
- **Returns Pydantic objects, not dicts**: `ollama.list()` returns Pydantic Model objects
  - Must access attributes directly: `model.model` or `model.name` (NOT `model.get("name")`)
  - Use `getattr(model, 'attribute', default)` for optional fields
- **Uses `num_predict` not `max_tokens`**: When calling `ollama.chat()`, pass `num_predict` in options
- **Streaming format**: Each chunk has structure `{"message": {"content": "..."}}`

#### Settings Widget Behavior
- **NumberInput sends 0 for empty**: When max_tokens input is empty/unlimited, widget sends `0`
  - Must convert `0 → None` before passing to `ModelParameters` (which requires ≥1 or None)
- **TextInput can send None**: System prompt field may be `None`, not just empty string
  - Must use `(value or "").strip()` before calling string methods
- **Select uses index**: Model dropdown uses `initial_index`, not `initial_value`
  - Must find index of current model in choices list
  - Implement fallback: exact match → base name match → default to index 0

#### Model Name Matching
- Models may have tags: `"llama3:latest"` vs `"llama3"`
- Settings dropdown shows full names with tags
- Session may store base name without tag
- Matching strategy:
  1. Try exact match: `"llama3:latest" == "llama3:latest"`
  2. Try base name match: `"llama3".split(":")[0] == "llama3:latest".split(":")[0]`
  3. Default to index 0 with warning log

#### Logging Architecture
- **Hierarchical loggers**: Each module gets its own logger via `logging.getLogger(__name__)`
- **Centralized configuration**: `src/config/logging.py` sets up handlers for all loggers
- **Per-run log files**: Each app run creates `logs/app/app_YYYY-MM-DD_HH-MM-SS.log`
- **Dual output**: Console (INFO+) and file (DEBUG+) with different formatters
- **Logger pattern in every module**:
  ```python
  import logging
  logger = logging.getLogger(__name__)

  logger.info("User-visible operation")
  logger.debug("Detailed diagnostic info")
  logger.error("Error occurred", exc_info=True)  # Include stack trace
  ```

### Message Flow

```
User sends message in UI
    ↓
@on_message handler (src/ui/chat.py)
    ↓
Check for system commands (/exit, /quit, /stop_ollama)
    ↓ Yes → handle_system_command()
    ↓ No
Check for model commands (/models browse, /models pull, etc.)
    ↓ Yes → handle_model_command()
    ↓ No
Build message history:
    1. Add system prompt (if set)
    2. Add chat history from session
    3. Add current user message
    ↓
Call chat_stream() from ollama_service
    ↓
Stream response chunks via async generator
    ↓
Update UI message in real-time (await msg.update())
    ↓
Save user message + assistant response to session history
```

### Settings Initialization Flow

```
@on_chat_start (src/ui/chat.py)
    ↓
Initialize session with defaults from config
    ↓
Get current session values (model, params, system_prompt)
    ↓
Call get_settings_config(current_model, current_params, current_system_prompt)
    ↓
Fetch local models via list_local_models()
    ↓
Find index of current model in choices (with fallback logic)
    ↓
Create widgets with initial values from session
    ↓
Send settings sidebar to UI
```

**Key Point**: Settings widgets MUST be initialized with current session values, not hardcoded defaults. Otherwise, changing settings shows validation errors or unexpected behavior.

### Command System

The app uses two command prefixes for special operations:

1. **`/models` commands** (handled by `src/ui/model_management.py`):
   - `/models help` - Show help
   - `/models list` - List local models
   - `/models browse [pattern]` - Browse cloud models (optional regex filter)
   - `/models pull <name>` - Download model
   - `/models delete <name>` - Delete model
   - `/models search <pattern>` - Search local + cloud with regex

2. **`/system` or direct commands** (handled by `src/ui/system_actions.py`):
   - `/exit` or `/quit` - Exit app
   - `/stop_ollama` - Stop Ollama daemon and exit
   - `/system help` - Show system help

Commands are detected by checking if `message.content.startswith()` matches the prefix.

## Common Gotchas

### 1. Settings Page Blank
**Symptom**: Settings sidebar shows no widgets or empty dropdowns
**Cause**: Model names are empty strings because code tried to access Pydantic objects as dicts
**Fix**: Use `model.model` or `model.name` instead of `model.get("name")`

### 2. Validation Error on Settings Update
**Symptom**: `1 validation error for ModelParameters max_tokens: Input should be greater than or equal to 1`
**Cause**: NumberInput widget sends `0` for empty field, but schema requires `≥1 or None`
**Fix**: Convert `0 → None` in `on_settings_update()` before creating `ModelParameters`

### 3. AttributeError on None String
**Symptom**: `'NoneType' object has no attribute 'strip'`
**Cause**: TextInput fields (like system_prompt) can send `None`
**Fix**: Use `(value or "").strip()` instead of `value.strip()`

### 4. Model Not Selected in Dropdown
**Symptom**: Settings shows wrong model selected after changing model
**Cause**: Mismatch between session model name and dropdown choices (e.g., `"llama3"` vs `"llama3:latest"`)
**Fix**: Implement base name matching fallback in model index lookup

### 5. Ollama Connection Errors
**Symptom**: `OllamaNotRunningError` or connection timeouts
**Cause**: Ollama daemon not running or wrong URL
**Fix**: Check `ollama serve` is running and `OLLAMA_BASE_URL` is correct in `.env`

## File Structure Context

```
src/
├── models/schemas.py          # Pydantic models - all data structures
├── services/                  # Business logic (stateless, testable)
│   ├── ollama_service.py     # Ollama API wrapper (chat, list, pull, delete)
│   ├── model_manager.py      # Cloud models + regex filtering
│   ├── session_manager.py    # Save/load chat sessions to disk
│   └── system_service.py     # Exit app, stop Ollama daemon
├── ui/                        # Chainlit decorators (UI layer)
│   ├── chat.py               # @on_chat_start, @on_message
│   ├── settings.py           # @on_settings_update, get_settings_config()
│   ├── model_management.py   # /models command handlers
│   ├── actions.py            # Message actions (save session)
│   └── system_actions.py     # /exit, /quit, @on_action callbacks
├── config/
│   ├── settings.py           # Environment config (loads .env)
│   └── logging.py            # Per-run log files with rotation
└── app.py                     # Entry point (imports all UI handlers)
```

**Entry point**: `main.py` imports `src/app`, which imports all UI handlers to register Chainlit decorators.

## Testing Conventions

- Tests live in `tests/` mirroring `src/` structure
- Use `pytest-asyncio` for async tests
- Mock Ollama SDK calls to avoid external dependencies
- Test coverage target: 80%+
- Use `@pytest.fixture` for common test setup (temp dirs, mock data)

## Configuration

Environment variables in `.env`:
- `OLLAMA_BASE_URL` - Ollama daemon URL (default: http://localhost:11434)
- `DEFAULT_MODEL` - Initial model selection (default: llama3)
- `DEFAULT_TEMPERATURE` - Initial temperature (default: 0.7)
- `DEFAULT_TOP_P` - Initial top_p (default: 0.9)
- `DEFAULT_MAX_TOKENS` - Initial max tokens (empty = unlimited)
- `LOG_LEVEL` - Logging verbosity (default: INFO)
- `LOG_DIR` - Log file directory (default: logs)
- `SESSION_DATA_DIR` - Chat session storage (default: data/sessions)

## Logging Best Practices

When adding new features:
1. Add `logger = logging.getLogger(__name__)` at module level
2. Log INFO for user-visible operations (model pull, settings update, etc.)
3. Log DEBUG for detailed flow (function entry, parameter values, API responses)
4. Log ERROR with `exc_info=True` for exceptions to capture stack traces
5. Include context in log messages (model name, session ID, operation type)

Example:
```python
import logging
logger = logging.getLogger(__name__)

def some_operation(model: str, param: int) -> None:
    logger.info(f"Starting operation with model: {model}")
    logger.debug(f"Parameters: param={param}")

    try:
        # ... do work ...
        logger.info("Operation completed successfully")
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise
```

## Prerequisites

- Python 3.13+
- Ollama daemon (https://ollama.com/)
- uv package manager (recommended)

## Quick Start for New Contributors

1. Clone repo and install dependencies:
   ```bash
   uv sync --all-extras
   ```

2. Copy environment config:
   ```bash
   cp .env.example .env
   ```

3. Start Ollama daemon (separate terminal):
   ```bash
   ollama serve
   ```

4. Run the app:
   ```bash
   uv run chainlit run main.py -w
   ```

5. Open browser at http://localhost:8000

6. Run tests before committing:
   ```bash
   uv run pytest
   ruff check src/ tests/ --fix
   ruff format src/ tests/
   ```
