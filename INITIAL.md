## FEATURE:

- Chainlit-based chatbot interface for local LLM models via Ollama (using Ollama Python SDK and REST API)
- Classic chat UI with message bubbles (user/assistant differentiation)
- Model selection dropdown to switch between available Ollama models
- Model management:
  - Browse and list all available models from Ollama Hub
  - Pull models from Ollama Hub to local storage
  - List all models that have been pulled locally
  - Regex filtering for model listings (e.g., filter by "gpt", "llama", etc.)
    - Filter available models from Ollama Hub
    - Filter locally pulled models
  - Delete locally stored models
  - API key configuration for Ollama official site API calls
- Conversation features:
  - Persistent chat history (save/load sessions)
  - Message actions (copy, regenerate, edit, etc.)
  - System prompt customization
  - Model parameter controls (temperature, top_p, max tokens)
- UI/UX:
  - Minimal, clean design inspired by modern chat interfaces
  - Dark/Light theme support
  - Responsive layout

## DEPENDENCIES

**Development & Project Management:**
- **uv** - Modern Python package and project manager
  - Project initialization and dependency management
  - Virtual environment handling
  - Fast package installation and resolution

**Environment Configuration:**
- **python-dotenv** - Environment variable management
  - Load environment variables from .env file
  - Secure API key and configuration storage
  - Separate configuration from code

**Code Quality:**
- **ruff** - Fast Python linter and formatter
  - Code linting for style and potential errors
  - Automatic code formatting
  - Import sorting and organization

**Testing:**
- **pytest** - Python testing framework
  - Unit testing for project components
  - Test discovery and execution
  - Fixtures and test organization

**LLM Integration:**
- **ollama** - Local LLM management and inference
  - Pull and manage local models
  - List available models
  - Run inference with streaming support
  - Model parameter configuration (temperature, top_p, max tokens)


## EXAMPLES:

examples/chatlint/app_actions.py – Adds interactive buttons and quick actions (e.g. "Explain", "Summarize") to Chainlit chat.
examples/chatlint/app_basic.py – Minimal Chainlit chatbot that echoes user input.
examples/chatlint/app_ollama.py – Connects Chainlit to a local Ollama model for non-streaming responses.
examples/chatlint/app_streaming.py – Streams model responses live into Chainlit message bubbles.
examples/chatlint/app_tools.py – Demonstrates sliders and user-configurable settings (like temperature) in Chainlit.
examples/ollama/app_ollama_chainlit.py – Full Chainlit integration using the official Ollama SDK with streaming output.
examples/ollama/ollama_chatloop.py – Interactive console chat loop maintaining conversation history.
examples/ollama/ollama_simple.py – Basic one-shot prompt using the Ollama SDK (non-streaming).
examples/ollama/ollama_streaming.py – Streams token chunks from the Ollama model in real time.
examples/ollama/ollama_streamloop.py – Streaming chat loop version showing incremental "typing" output.
examples/ollama_interface/models_list_and_filter.py – Lists local and online models and filters them by regex (e.g. "gpt").

## DOCUMENTATION:

**Ollama (Python SDK)**
- Python SDK Documentation: https://github.com/ollama/ollama-python
- REST API Reference: https://github.com/ollama/ollama/blob/main/docs/api.md

**💬 Chainlit**
- Documentation: https://docs.chainlit.io
- Pure Python Quick Start: https://docs.chainlit.io/get-started/pure-python

**🧰 uv**
- Documentation: https://docs.astral.sh/uv
- CLI Reference: https://docs.astral.sh/uv/reference/cli

**🧹 Ruff**
- Documentation: https://docs.astral.sh/ruff
- Rules Reference: https://docs.astral.sh/ruff/rules

**Ollama documentation (terminal / CLI + general docs)**
- Ollama main docs (includes install, quickstart, etc.):https://docs.ollama.com 
- Ollama CLI Reference (terminal commands like ollama run, ollama pull, ollama list, etc.):https://docs.ollama.com/cli 
- Ollama Cloud docs (includes API key, https://ollama.com/api/tags listing cloud models):https://docs.ollama.com/cloud

**Pytest**
- https://docs.pytest.org/en/stable/

## OTHER CONSIDERATIONS:

- Use environment variables for API key configuration instead of hardcoded model strings, .env
- Keep agents simple - default to string output unless structured output is specifically needed
- Always include comprehensive testing with TestModel for development
