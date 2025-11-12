# Ollama Chainlit Chatbot 🦙

A production-ready Chainlit-based chat interface for interacting with local Ollama LLM models. Chat with powerful AI models running entirely on your machine - no cloud dependency, complete privacy.

## Requirements

Before getting started, ensure you have the following installed:

| Requirement | Minimum Version | Installation Guide |
|-------------|----------------|-------------------|
| **Python** | 3.13+ | [Download Python](https://www.python.org/downloads/) |
| **Ollama** | Latest | [Install Ollama](https://ollama.com/download) |
| **uv** (recommended) | Latest | [Install uv](https://docs.astral.sh/uv/getting-started/installation/) |

## Features

- 💬 **Real-time Streaming Chat** - Stream responses from local Ollama models with live updates
- 🎛️ **Model Selector Dropdown** - Easy model switching via top-left dropdown menu
- 🗑️ **UI Model Management** - Browse, download, and delete models with one-click buttons
- 📁 **File Upload Support** - Upload and discuss documents with your AI assistant
- ⚙️ **Customizable Parameters** - Fine-tune temperature, top_p, and max_tokens via settings panel
- 🎨 **Modern UI** - Clean, responsive design with dark/light theme support
- 📝 **Production Logging** - Daily rotating logs with configurable levels
- 🔒 **Type Safety** - Full Pydantic validation and MyPy type checking
- ✅ **Comprehensive Tests** - 80%+ test coverage with pytest

## Installation

### 1. Clone the Repository

```bash
git clone git@github.com:OmerBS123/ollama-chat-interface.git
cd oss-chatbot
```

### 2. Install Dependencies

```bash
uv sync --all-extras
```

### 3. Configure Environment (Optional)

The repository includes a `.env.example` file as a template with all available configuration options. Copy it to create your own `.env` file:

```bash
cp .env.example .env
# Edit .env with your custom settings if needed
```

> **Note:** The `.env` file is gitignored for security. Never commit your `.env` file to version control. The `.env.example` file is intentionally tracked to provide configuration guidance.

For detailed information about all available environment variables and how to configure them, see the [Configuration](#configuration) section.

### 4. Start Ollama Daemon

```bash
# In a separate terminal window
ollama serve
```

### 5. Run the Application

```bash
uv run chainlit run main.py -w
```

### 6. Open Your Browser

Navigate to: `http://localhost:8000`

> **Note:** No need to pre-download models! Use the model dropdown to auto-download any model from Ollama Hub.

## Usage

### Quick Start (3 Steps)

1. **Select a Model**
   - Click the **model dropdown** in the top-left corner
   - Choose a downloaded model or select a cloud model (auto-downloads)

2. **Start Chatting**
   - Type your message in the input box
   - Press Enter and watch the response stream live

3. **Upload Files** (Optional)
   - Click the 📎 attachment icon
   - Upload documents to discuss with the AI

### Model Management

#### Selecting Models

**Model Dropdown (Top-Left):**
- Shows all downloaded models (marked with ✅)
- Shows popular cloud models available for download (marked with ☁️)
- Click any model to switch instantly
- Selecting a cloud model triggers automatic download with progress bar

#### Deleting Models

**Manage Models Button:**
1. Click the **🗑️ Manage Models** button in the welcome message or action bar
2. View all downloaded models with size information (displayed in GB)
3. Click **🗑️ Delete [model-name]** for the model you want to remove
4. Confirm deletion (includes warning that chat will refresh)
5. Model is deleted and page refreshes automatically

**Layout:**
- One model per line for easy scanning
- Shows model name, family, and size
- Warning message about chat refresh included

### Customizing Parameters

**Settings Panel (Top-Right ⚙️ icon):**

1. **Temperature** (0-2)
   - Controls response randomness
   - 0.0 = Deterministic, focused (best for code/facts)
   - 0.7 = Balanced creativity (default)
   - 2.0 = Very creative (best for creative writing)

2. **Top P** (0-1)
   - Nucleus sampling threshold
   - 0.9 = Recommended default
   - Higher = more diverse word choices

3. **Max Tokens**
   - Maximum response length
   - 0 = Unlimited
   - Set to limit response size

4. **System Prompt**
   - Custom instructions to guide assistant behavior
   - Example: "You are a helpful Python expert who writes clean code"
   - Applies to all subsequent messages

### File Upload

**How to Upload Files:**
1. Click the 📎 **attachment icon** next to the message input
2. Select one or more files from your computer
3. Type your question about the file(s)
4. Press Enter

**Supported:**
- Text files (.txt, .md, .py, .js, etc.)
- Documents (.csv, .json, .xml, etc.)
- Any UTF-8 encoded file

**How It Works:**
- File content is read and appended to your message
- The AI receives both your question AND the file content
- Files are formatted in markdown code blocks for clarity

### Stopping the Application

**UI Button (Recommended):**
- Click the **🛑 Stop Ollama & Exit** button
- Stops the Ollama daemon and exits the app gracefully

**Keyboard:**
- Press `Ctrl+C` (or `Cmd+C` on Mac) in the terminal

## Configuration

### Environment Variables (.env)

All configuration is done via a `.env` file. A `.env.example` file is provided in the repository as a template showing all available options with default values.

**To configure:**
1. Copy `.env.example` to `.env`: `cp .env.example .env`
2. Edit `.env` with your preferred settings
3. Restart the application for changes to take effect

**Available options:**

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=  # Optional: Only needed for hosted/cloud Ollama instances

# Application Defaults
DEFAULT_MODEL=llama3
DEFAULT_TEMPERATURE=0.7
DEFAULT_TOP_P=0.9
DEFAULT_MAX_TOKENS=  # Empty = unlimited

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_DIR=logs

# Session Storage
SESSION_DATA_DIR=data/sessions
```

### Configuration Details

**OLLAMA_BASE_URL**: URL where Ollama daemon is running
- Default: `http://localhost:11434`
- Change this only if running Ollama on a different host/port

**OLLAMA_API_KEY**: API key for authentication *(Optional)*
- **Local Ollama (default)**: Leave empty - no API key needed
- **Hosted/Cloud Ollama**: Required - get from your Ollama Cloud dashboard
- **How to get API key**:
  1. Visit [Ollama Cloud](https://ollama.com/) (if using hosted version)
  2. Sign in to your account
  3. Go to Settings → API Keys
  4. Generate a new API key
  5. Copy and paste into `.env` file

> **Note:** For most users running Ollama locally, you **do not need** an API key. Leave this field empty.

## Architecture

### Project Structure

```
oss-chatbot/
├── src/
│   ├── models/
│   │   └── schemas.py              # Pydantic models (ChatMessage, ModelInfo, ModelParameters)
│   ├── services/
│   │   ├── ollama_service.py      # Ollama API wrapper (chat, pull, delete, list)
│   │   ├── model_manager.py       # Cloud model discovery and filtering
│   │   ├── session_manager.py     # Chat session persistence
│   │   └── system_service.py      # System operations (exit, stop daemon)
│   ├── ui/
│   │   ├── chat.py                # Chat handlers (@on_message, @on_chat_start)
│   │   ├── chat_profiles.py       # Model dropdown configuration
│   │   ├── model_management_button.py  # Model deletion UI
│   │   ├── settings.py            # Settings panel (@on_settings_update)
│   │   ├── actions.py             # Message actions
│   │   └── system_actions.py      # System button handlers
│   ├── config/
│   │   ├── settings.py            # Environment configuration
│   │   └── logging.py             # Logging setup (daily rotation)
│   ├── data.py                     # Data layer for sessions
│   └── app.py                     # Application entry point
├── tests/
│   ├── unit/                      # Unit tests for services
│   ├── integration/               # Integration tests for flows
│   └── e2e/                       # End-to-end tests
├── main.py                         # Entry point
├── chainlit.md                     # Welcome message
├── .env.example                    # Environment template
└── pyproject.toml                  # Dependencies
```

### Key Design Patterns

1. **Service Layer Pattern** - Business logic separated from UI handlers
2. **Type-Safe Models** - Pydantic validates all data at runtime
3. **Async First** - All I/O operations use async/await
4. **Streaming Responses** - Real-time token streaming for better UX
5. **Production Logging** - Structured logs with daily rotation

## Development

### Running in Development Mode

```bash
# With watch mode (auto-reload on changes)
uv run chainlit run main.py -w
```

### Running Tests

> **⚠️ Important:** Always run tests using `uv run pytest`, NOT just `pytest`. This ensures tests run in the correct environment with all dependencies installed. See [Troubleshooting](#tests-failing-with-import-errors) if you get import errors.

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test category
uv run pytest tests/unit/ -v          # Unit tests only
uv run pytest tests/integration/ -v   # Integration tests only
uv run pytest tests/e2e/ -v           # E2E tests only

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing
```

### Code Quality

```bash
# Linting with auto-fix
ruff check src/ tests/ --fix

# Formatting
ruff format src/ tests/

# Type checking (if mypy installed)
mypy src/
```

### Adding New Features

1. **Add service logic** in `src/services/` for backend functionality
2. **Add UI handlers** in `src/ui/` for Chainlit decorators
3. **Add Pydantic models** in `src/models/schemas.py` for new data structures
4. **Add tests** in `tests/unit/` or `tests/integration/`
5. **Run validation** with `ruff check` and `pytest`

## Logging

### Log Configuration

**Environment Variables:**
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR (Default: INFO)
- `LOG_DIR` - Log directory (Default: logs)

**Log File Structure:**
```
logs/
└── app/
    ├── app_2025-01-12.log    # Today's log
    ├── app_2025-01-11.log    # Yesterday's log
    └── ...                   # Rotates daily, keeps 30 days
```

**Viewing Logs:**
```bash
# Tail today's logs
tail -f logs/app/app_$(date +%Y-%m-%d).log

# Search for errors
grep ERROR logs/app/*.log

# Search for specific model operations
grep "llama3" logs/app/*.log
```

## Troubleshooting

### Ollama Not Running

**Error:** `Ollama is not running`

**Solution:**
```bash
# Start Ollama daemon in a separate terminal
ollama serve
```

### Ollama "Address Already in Use"

**Error:** `Error: listen tcp 127.0.0.1:11434: bind: address already in use`

**This means Ollama is already running!** This is not an error - it means the daemon is active.

**To verify Ollama is running:**
```bash
# Check if Ollama is responding
curl http://localhost:11434/api/tags

# Or check for the process
lsof -ti :11434
```

If you get a response, Ollama is working correctly. You can proceed to run the chat application.

### No Models Downloaded

**Solution:**
1. Click the **model dropdown** (top-left)
2. Select any cloud model (marked with ☁️)
3. Wait for automatic download with progress bar
4. Model will be ready to use

### File Upload Not Working

**Issue:** Uploaded file not recognized by AI

**Possible Causes:**
- File is binary (images, PDFs - not yet supported)
- File encoding is not UTF-8

**Solution:**
- Use text-based files (.txt, .md, .py, .json, etc.)
- Ensure files are UTF-8 encoded

### Model Deletion Issues

**Issue:** Model deletion doesn't complete or page gets stuck

**Solution:**
- Refresh the browser (F5)
- The model will still be deleted even if UI seems stuck

### Connection Timeout

**Error:** `Connection timeout` or `Network error`

**Solution:**
1. Verify Ollama is running: `ollama serve`
2. Test connection: `curl http://localhost:11434/api/tags`
3. Check `OLLAMA_BASE_URL` in `.env` is correct (should be `http://localhost:11434`)

### Tests Failing with Import Errors

**Error:** `ModuleNotFoundError: No module named 'ollama'` or `ModuleNotFoundError: No module named 'dotenv'`

**Cause:** Running `pytest` directly instead of `uv run pytest`

**Why this happens:**
- The project uses `uv` to manage dependencies in a virtual environment
- Running `pytest` directly uses your system/conda Python environment
- Project dependencies (ollama, chainlit, dotenv, etc.) are only installed in the uv environment

**Solution:**
```bash
# ❌ WRONG - uses system Python
pytest

# ✅ CORRECT - uses uv environment with all dependencies
uv run pytest
```

**Verify your setup:**
```bash
# Check uv is installed
uv --version

# Sync all dependencies (including dev/test dependencies)
uv sync --all-extras

# Run tests with uv
uv run pytest -v
```

## API Reference

### Ollama Service

```python
from src.services.ollama_service import (
    chat_stream,
    list_local_models,
    pull_model,
    pull_model_with_progress,
    delete_model
)

# Stream chat response
async for chunk in chat_stream(messages, model, params):
    print(chunk, end="")

# List local models
models = list_local_models()  # Returns list[ModelInfo]

# Pull model with progress
async for progress in pull_model_with_progress("llama3"):
    print(f"Progress: {progress}")

# Delete model
delete_model("mistral:latest")
```

### Model Manager

```python
from src.services.model_manager import list_cloud_models, filter_models

# Fetch cloud models from Ollama Hub
cloud_models = list_cloud_models()

# Filter by pattern
filtered = filter_models(models, r"llama.*3")
```

### Session Manager

```python
from src.services.session_manager import save_session, load_session

# Save session
save_session(
    session_id="abc123",
    model_name="llama3",
    messages=[...],
    parameters=ModelParameters(...),
    system_prompt="You are helpful"
)

# Load session
session = load_session("abc123")
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following the existing code style
4. **Add tests** for new functionality
5. **Run tests**: `uv run pytest`
6. **Check code quality**:
   ```bash
   ruff check src/ tests/ --fix
   ruff format src/ tests/
   ```
7. **Commit changes**: `git commit -m "Add amazing feature"`
8. **Push to branch**: `git push origin feature/amazing-feature`
9. **Open a Pull Request**

### Code Style

- Use type hints for all function parameters and returns
- Follow PEP 8 style guide (enforced by ruff)
- Add docstrings to all public functions
- Keep functions focused and small
- Write tests for new features

## License

<!-- License information will be added here -->

## Acknowledgments

- [Chainlit](https://chainlit.io/) - Modern chat UI framework
- [Ollama](https://ollama.com/) - Local LLM runtime
- [Pydantic](https://pydantic.dev/) - Data validation
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the [Chainlit docs](https://docs.chainlit.io/)
- Check the [Ollama docs](https://docs.ollama.com/)
