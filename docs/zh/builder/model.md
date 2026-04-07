# 模型接入

## 目标

用最少样板代码把模型接入到多步 Agent 循环中，并保证可调试性。

## 默认调用路径

当 `AgentModule.decide(...)` 返回 `None` 时：

1. Engine 调 `agent.prepare(state)`
2. Engine 拼接 system prompt
3. Engine 注入 history messages
4. Engine 调 `agent.llm(messages)`
5. parser 把模型输出转成 `Decision`

## 最小接入示例

```python
from qitos import AgentModule
from qitos.kit import ReActTextParser

class MyAgent(AgentModule):
    def __init__(self, llm):
        super().__init__(tool_registry=..., llm=llm, model_parser=ReActTextParser())

    def build_system_prompt(self, state):
        return "你是严谨的代码智能体。"

    def prepare(self, state):
        return f"任务: {state.task}\n步数: {state.current_step}/{state.max_steps}"

    def decide(self, state, observation):
        return None
```

## 推荐配置方式

用环境变量，不要把 key 写死在代码里：

```bash
export OPENAI_BASE_URL="https://api.siliconflow.cn/v1/"
export OPENAI_API_KEY="<your_key>"
```

## 一等公民模型适配器

QitOS 现在同时提供原生接口与兼容接口的一等模型类：

- `OpenAIModel`
- `OpenAICompatibleModel`
- `AnthropicModel`
- `GeminiModel`
- `LiteLLMModel`
- `OllamaModel`
- `LMStudioModel`

最小示例：

```python
from qitos.models import AnthropicModel, GeminiModel, LiteLLMModel, LMStudioModel, OllamaModel

claude = AnthropicModel(model="claude-3-5-sonnet-latest", api_key="...")
gemini = GeminiModel(model="gemini-2.5-flash", api_key="...")
litellm = LiteLLMModel(model="anthropic/claude-3-5-sonnet-latest", api_key="...")
ollama = OllamaModel(model="llama3.1")
lmstudio = LMStudioModel(model="local-model")
```

推荐环境变量：

```bash
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
export LITELLM_MODEL="anthropic/claude-3-5-sonnet-latest"
export LITELLM_API_KEY="..."
export OLLAMA_HOST="http://localhost:11434"
export LM_STUDIO_BASE_URL="http://localhost:1234/v1"
```

如果你偏好纯环境变量接入，`ModelFactory.from_env()` 现在也会自动识别
Anthropic、Gemini、LiteLLM、Ollama 和 LM Studio。

## 可靠性检查

1. parser 要和模型输出协议匹配（JSON/XML/ReAct/函数式文本）。
2. prompt 里要明确要求输出格式。
3. parser 需要对截断或格式错误输出有降级处理。
4. trace 里要能看见模型名和 parser 名。

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
