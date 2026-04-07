# Model Integration

## Goal

Connect your model in a way that is robust for multi-step agent runs.

## Default Engine-driven model path

When `AgentModule.decide(...)` returns `None`:

1. Engine calls `agent.prepare(state)`.
2. Engine adds system prompt from `build_system_prompt`.
3. Engine retrieves history messages.
4. Engine calls `agent.llm(messages)`.
5. Parser maps model output to `Decision`.

## Minimal model wiring

```python
from qitos import AgentModule
from qitos.kit import ReActTextParser

class MyAgent(AgentModule):
    def __init__(self, llm):
        super().__init__(tool_registry=..., llm=llm, model_parser=ReActTextParser())

    def build_system_prompt(self, state):
        return "You are a precise coding assistant."

    def prepare(self, state):
        return f"Task: {state.task}\nStep: {state.current_step}/{state.max_steps}"

    def decide(self, state, observation):
        return None
```

## Config recommendation

Use env vars, not hardcoded keys:

```bash
export OPENAI_BASE_URL="https://api.siliconflow.cn/v1/"
export OPENAI_API_KEY="..."
```

## First-class provider adapters

QitOS ships first-class adapters for both native APIs and compatibility
endpoints:

- `OpenAIModel`
- `OpenAICompatibleModel`
- `AnthropicModel`
- `GeminiModel`
- `LiteLLMModel`
- `OllamaModel`
- `LMStudioModel`

Minimal examples:

```python
from qitos.models import AnthropicModel, GeminiModel, LiteLLMModel, LMStudioModel, OllamaModel

claude = AnthropicModel(model="claude-3-5-sonnet-latest", api_key="...")
gemini = GeminiModel(model="gemini-2.5-flash", api_key="...")
litellm = LiteLLMModel(model="anthropic/claude-3-5-sonnet-latest", api_key="...")
ollama = OllamaModel(model="llama3.1")
lmstudio = LMStudioModel(model="local-model")
```

Recommended environment variables:

```bash
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
export LITELLM_MODEL="anthropic/claude-3-5-sonnet-latest"
export LITELLM_API_KEY="..."
export OLLAMA_HOST="http://localhost:11434"
export LM_STUDIO_BASE_URL="http://localhost:1234/v1"
```

If you prefer environment-driven wiring, `ModelFactory.from_env()` also detects
Anthropic, Gemini, LiteLLM, Ollama, and LM Studio.

## Reliability checklist

1. Parser supports your output format (JSON/XML/ReAct/function-like).
2. Prompt instructs exact output protocol.
3. Parser has fallback behavior for malformed/truncated outputs.
4. Trace includes model name and parser name for audit.

## Source Index

- [qitos/core/agent_module.py](https://github.com/Qitor/qitos/blob/main/qitos/core/agent_module.py)
- [qitos/models/anthropic.py](https://github.com/Qitor/qitos/blob/main/qitos/models/anthropic.py)
- [qitos/models/gemini.py](https://github.com/Qitor/qitos/blob/main/qitos/models/gemini.py)
- [qitos/models/litellm.py](https://github.com/Qitor/qitos/blob/main/qitos/models/litellm.py)
- [qitos/models/openai.py](https://github.com/Qitor/qitos/blob/main/qitos/models/openai.py)
- [qitos/models/local.py](https://github.com/Qitor/qitos/blob/main/qitos/models/local.py)
- [qitos/kit/parser/react_parser.py](https://github.com/Qitor/qitos/blob/main/qitos/kit/parser/react_parser.py)
- [qitos/kit/parser/func_parser.py](https://github.com/Qitor/qitos/blob/main/qitos/kit/parser/func_parser.py)
- [qitos/engine/engine.py](https://github.com/Qitor/qitos/blob/main/qitos/engine/engine.py)
