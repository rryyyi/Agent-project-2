# 模型服务配置

应用从仓库根目录 `.env` 加载配置，默认模型地址为 SiliconFlow 的 OpenAI 兼容接口。完整变量参见 [.env.example](.env.example)，配置读取逻辑见 [config.py](config.py)。

## 配置项

| 变量 | 默认值 | 当前用途 |
| --- | --- | --- |
| `SILICONFLOW_BASE_URL` | `https://api.siliconflow.cn/v1` | 模型服务根地址 |
| `SILICONFLOW_API_KEY` | 空 | 点位客户端 Bearer 认证 |
| `CHAT_MODEL` | `Qwen/Qwen3.5-9B` | 聊天模型，亦作为 STE/SGE 模型名 |
| `POINT_ANALYSIS_MODEL` | 与 `CHAT_MODEL` 相同 | 点位分析与复审模型 |
| `POINT_ANALYSIS_BATCH_SIZE` | `12` | 每批分析点位数，最小为 1 |
| `POINT_ANALYSIS_MAX_BUNDLE_CHARS` | `60000` | 证据包正文预算，最小为 10000；来源标记另计 |
| `MODEL_TIMEOUT` | `180` | 每次 HTTP 调用超时秒数 |
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-0.6B` | 已封装客户端，诊断检索尚未使用 |
| `RERANKER_MODEL` | `Qwen/Qwen3-Reranker-0.6B` | 已封装客户端，诊断检索尚未使用 |

模型可用性、配额与标识以服务提供方为准。点位每批至少进行分析与复审两次调用；较大的证据包会增加上下文和调用成本。证据包超过预算时会截断，当前没有检索式补取机制。

## 当前调用行为

| 链路 | 实现 | 认证与失败行为 |
| --- | --- | --- |
| PLC 点位分析/复审 | `services/siliconflow_client.py` | 使用 API Key；传输异常最多尝试 3 次；缺少凭证、HTTP 错误或解析失败使任务失败 |
| STE/SGE 抽取 | 旧版 `httpx` 直接调用 | URL/模型取自配置，但未传递 API Key；调用失败时返回标记为 `mock` 的规则结果 |
| 诊断生成 | 旧版 `httpx` 直接调用 | 未传递 API Key；调用失败时使用检索证据生成候选 |

因此，配置 SiliconFlow Key 后，点位链路使用认证模型调用；旧版解析/诊断不会自动获得该认证能力，连接需要认证的服务时可能进入降级路径。需要检查 STE/SGE 产物中的 `mock`、`error`，不能仅根据任务 `completed` 判断模型已执行成功。

`ENABLE_MODEL_CALL` 当前在代码中固定为 `True`，并非可通过 `.env` 设置的开关。统一旧链路与认证客户端、显式暴露降级状态，是后续维护优先项。

## 历史本地模型脚本

[scripts/setup_model_services.ps1](scripts/setup_model_services.ps1) 与 [scripts/start_model_services.ps1](scripts/start_model_services.ps1) 保留早期 llama.cpp 模型下载和双端口启动流程：Mistral-7B 使用 `8080`，Pixtral-12B 使用 `8081`。模型文件位于 `models/gguf/`，已被 Git 忽略。

当前 `config.py` 不读取独立 `STE_URL / SGE_URL` 环境变量，统一由 `SILICONFLOW_BASE_URL` 派生请求地址。**仅运行历史脚本不会自动将当前应用切换至两个本地端点。** 若希望继续使用双端口部署，需要显式改造适配器和配置、匹配实际模型别名并验证接口；该流程不是当前默认启动方式。

## 配置检查

- 将 `.env.example` 复制为 `.env`，填写有效 Key 和账户可用模型。
- 先启动 API，访问 `/health` 检查进程存活，再用 [合成资料](examples/README.md) 发起点位任务验证真实模型连接。
- 若失败，查看任务 `error`，区分缺少凭证、服务权限/限流、传输超时与模型 JSON 不符合约定。
- `.env`、模型权重和运行资料均不纳入版本管理；问题报告中只提供脱敏配置。
