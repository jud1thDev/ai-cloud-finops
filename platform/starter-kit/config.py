"""Model configuration — switch between Ollama (local), OpenAI, Claude."""

import os

# ── Choose your model provider ──
# Options: "ollama", "openai", "claude"
MODEL_PROVIDER = "ollama"

# ── Ollama (local, free) ──
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:14b"  # Recommended: qwen2.5:14b, llama3.1, mistral

# ── OpenAI ──
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"

# ── Claude ──
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ── General ──
MAX_TOKENS = 4096
TEMPERATURE = 0.1  # Low for consistent analysis
