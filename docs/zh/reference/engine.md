# Engine（API 参考）

## 职责

`Engine` 是唯一运行时内核，负责：

- 循环编排
- task/env 预检
- action 执行
- budget 与 stop 判定
- hooks/events/trace
- 面向 LLM 的默认上下文长度 telemetry
- 默认的上下文 compact 协调

## 运行链路

每一步：

1. DECIDE
2. ACT
3. REDUCE
4. CHECK_STOP

当 `agent.decide(...)` 返回 `None` 时，DECIDE 阶段会调用 `prepare(state)`。

## 默认模型路径

当 `decide` 返回 `None`，Engine 会：

1. `prepared = agent.prepare(state)`
2. 组装 messages（system + history + 当前 user 输入）
3. `raw = agent.llm(messages)`
4. parser 解析成 `Decision`

## 常用参数

- `env`
- `history_policy`
- `context_config`
- `search`
- `critics`
- `hooks`
- `trace_writer`

## Context Management

对带 LLM 的 agent，Engine 现在默认记录每次请求的上下文指标：

- `input_tokens_total`
- `output_tokens`
- `history_tokens`
- `prepared_tokens`
- `occupancy_ratio`
- 运行累计 token totals

QiTOS 还会先根据常见模型 id 自动推断更准确的 `context_window`，
只有在无法识别时才回退到通用默认值。如果你明确知道某个模型的
上下文上限不同，仍然可以在模型适配器里显式覆盖。

当 history 触发 compact 或 warning 时，这些信息会进入：

- runtime events
- `records[*].context`
- trace manifest summary
- terminal UI
- qita board / view / replay

对大多数用户来说，更推荐直接走：

```python
agent.run(task, workspace="./playground", max_steps=8)
```

只有当你需要把某一套 runtime 配置复用到很多次运行里时，才建议直接手动构造 `Engine(...)`。

## 返回结果

`Engine.run(...)` 返回：

- `state`
- `records`
- `events`
- `step_count`
- `task_result`（可选）

## 最小用法

```python
result = my_agent.run(
    task="做点什么",
    workspace="./playground",
    max_steps=8,
    return_state=True,
)
print(result.state.final_result, result.state.stop_reason)
```
