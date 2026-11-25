# 贡献与验证规范

请先阅读 [项目入口](README.md)、[架构说明](docs/architecture.md) 与 [仓库指令](AGENTS.md)。提交应能够说明具体场景、行为变化和验证证据。

## 开发环境

按 README 创建 Python 环境、安装运行依赖后：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

OCR 安装需匹配平台支持。点位测试使用替代分析函数隔离外部模型，但导入应用仍需要运行依赖；测试通过不代表真实 OCR 或模型服务通过验证。

## 按变更范围验证

| 变更 | 最低验证 |
| --- | --- |
| 文档与示例 | Markdown 检查、相对链接、命令/字段与代码一致、示例格式正确 |
| 点位规则/API | 相关 pytest；需要时补充无证据、伪造引用与冲突案例 |
| 解析/诊断 | 相关服务或测试；说明模型正常与降级路径 |
| 前端 | 启动页面检查布局、交互、上传、进度、失败与空状态 |
| 模型接入 | 脱敏配置、真实接口检查、输出契约和失败行为 |

轻量静态检查：

```bash
python -m compileall -q main.py config.py models routers services tests
npx --yes markdownlint-cli2@0.17.2 "**/*.md" "#node_modules" "#.venv" "#storage" "#runtime" "#models/gguf" "#.git" "#.superpowers"
git diff --check
```

GitHub Actions 仅执行 Markdown 与 Python 语法检查，不安装 OCR、不请求模型、不声称运行完整业务测试。真实服务验证应单独记录模型名、数据版本、依赖版本与结果。

## 提交要求

- 一个提交围绕一个清晰目的，标题可使用 `docs:`、`fix:`、`feat:`、`chore:`。
- PR 说明问题、修改后的行为、验证方式和未验证范围；不要只罗列修改文件。
- 不添加未经测量的性能数字，不将设计路线图描述为已实现能力。
- 示例使用合成资料；不要提交 `.env`、API Key、真实客户资料、生产点表、模型权重或 `storage/` 产物。
- 新增 Agent 角色时同时说明输入输出、失败行为、证据要求和可检查产物。

报告问题时可使用仓库 Issue 模板，并附最小复现步骤与脱敏信息。仓库尚未声明许可证，贡献或复用涉及授权时请先与作者确认。
