# 合成演示资料

`plc/points.csv` 和 `plc/logic.scl` 描述一个虚构输送设备的四个点位，供点位工作台演示。资料不来源于生产系统，SCL 文件仅作为可读逻辑文本，不是可编译部署的 PLC 工程。

## 操作步骤

1. 按 [README](../README.md) 安装运行依赖、配置模型并启动 API。
2. 打开 <http://127.0.0.1:8000/point-analysis>。
3. 同时选择 [points.csv](plc/points.csv) 和 [logic.scl](plc/logic.scl)，点击开始分析。
4. 等待分析、复审与本地校验结束，查看各点位的身份、引用、下游影响、反事实与验证状态。
5. 下载 CSV，核对原始四列被保留，分析列追加在其后。

不预设每个点位都应获得高分；资料只包含一个简单逻辑路径，模型也可能返回资料不足或候选。使用合成资料的目标是理解输入输出与审查流程。

## 可手动检查的证据

- `Network 1`：安全门与过载状态共同影响 `RunPermissive`。
- `Network 2`：许可与启动请求共同影响 `RunCommand`。
- `Network 3`：给出三种状态组合供人工核对，并明确它们不是实际执行记录。

打开结果详情，确认 `source_file` 指向 `logic.scl`、`quote` 是文件原文、`location` 能帮助人工找到对应 Network。当前本地校验会检查引用原文存在与位置字段非空，不对 Network 位置执行解析验证。

## 凭证与验证范围

真实模型调用需要有效服务凭证，可能产生费用。无凭证时可阅读数据与源码，但不能声称已完成真实模型端到端验证。现有测试通过替代模型分析验证规则与 API，见 [tests/test_point_analysis.py](../tests/test_point_analysis.py)。
