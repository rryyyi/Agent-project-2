# 仓库维护验证记录

本记录对应 2026-11-25 的 README 与仓库维护变更。变更范围为文档、合成示例、配置示例、依赖清单、忽略规则和 GitHub 检查，不修改业务实现。

## 已执行

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| Markdown lint | 通过 | 仓库 Markdown，使用 `markdownlint-cli2@0.17.2` |
| 相对链接与锚点 | 通过 | 本地文件目标及文档标题锚点 |
| Python compileall | 通过 | `main.py config.py models routers services tests`；只检查语法 |
| Git diff whitespace | 通过 | `git diff --check` |
| 现有评分门槛测试 | 通过 | 隔离加载点位服务源码，执行 `test_score_requires_logic_counterfactual_and_verified_citations` |
| 现有引用校验测试 | 通过 | 隔离加载点位服务源码，执行 `test_citation_verification_checks_source_file_quote_and_location` |
| 合成 PLC 输入 | 通过 | 4 条点表记录、可读逻辑证据包、示例原文引用 |
| 文档与源码自审 | 完成 | API、模型配置、状态流、评分公式、能力边界与评估口径 |

规则检查通过 AST 去除点位服务的配置/模型导入，保留并执行原服务函数及两项现有测试断言，使用临时目录隔离数据。它验证这些函数的局部行为，不替代应用导入或完整 pytest。

## 未通过或未执行

完整 `python -m pytest -q` 在收集时因环境缺少 `aiofiles` 而失败；该环境也未安装 PaddleOCR/PaddlePaddle，未继续执行 API 测试。未以替代 OCR 模块冒充完整环境测试通过。

当前验证主机为 Windows、Python 3.14。未执行 README 推荐的 Python 3.11 全量依赖安装、真实模型请求、OCR、UI 浏览器交互或真实工业数据诊断。现有依赖清单未锁定版本，安装兼容性仍需在目标环境检查。

本次没有子代理工具，采用作者单独一轮自审，未获得独立评审。GitHub Actions 执行结果请查看仓库 Actions 页面；本地静态检查通过不代表远程工作流已经运行成功。
