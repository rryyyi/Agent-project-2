# 工业点位重要性分析

启动 FastAPI 后打开 `/point-analysis`，上传包含 `Device、Name、Address、Type` 四列的 CSV 点位表，并同时上传 TIA Portal 工程导出、SCL/AWL/STL 或可读 XML 等 PLC 逻辑文件。程序分批调用配置的大模型生成分析，再用第二轮模型复审；本地校验引用原文是否存在，并按逻辑关键路径、运行门槛、安全联锁、下游扇出、影响范围、反事实场景、证据质量和替代路径计算确定性分数。

网页支持任务进度、点位搜索和状态筛选、证据详情、分页及 CSV 导出。导出保留点表原始四列，并追加重要性评分、验证状态、逻辑引用数、下游影响、反事实场景、证据定位和结论。只有模型复审通过、逻辑引用和反事实关系成立、引用位置及原文通过本地校验且达到评分门槛时才会标为“已验证”；高分但缺少任一验证条件的点位显示为候选。二进制 TIA 工程文件本身不能替代可读的 PLC 逻辑导出，资料不足时系统会显式提示，不会将名称推断称为已验证结论。

分析接口：

- `POST /api/v1/point-analysis/runs`：多文件表单上传并启动任务。
- `GET /api/v1/point-analysis/runs/{run_id}`：查询任务状态和进度。
- `GET /api/v1/point-analysis/runs/{run_id}/results`：分页查询，支持 `page`、`page_size`、`status`、`search`。
- `GET /api/v1/point-analysis/runs/{run_id}/download`：下载点位分析 CSV。

上传限制为 1000 个文件、单次总计 2 GB；ZIP 解压限制和文件类型处理见分析服务实现。模型配置使用 `.env` 中的 `POINT_ANALYSIS_MODEL`、`POINT_ANALYSIS_BATCH_SIZE` 和 `POINT_ANALYSIS_MAX_BUNDLE_CHARS`。
