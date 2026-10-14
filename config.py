"""
全局配置：路径、模型服务地址、开关。
所有存储目录在这里统一定义，其他模块引用。
"""
from pathlib import Path
import os

from dotenv import load_dotenv

# ── 基础目录 ──
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
STORAGE_DIR = BASE_DIR / "storage"

# ── 各阶段产物目录 ──
ORIGINALS_DIR = STORAGE_DIR / "originals"   # 原始上传文件
PARSED_DIR = STORAGE_DIR / "parsed"         # 解析中间结果 Document IR
EXTRACTED_DIR = STORAGE_DIR / "extracted"   # STE/SGE 抽取结果
GRAPH_DIR = STORAGE_DIR / "graph"           # 知识图谱
META_DIR = STORAGE_DIR / "meta"             # 文档元数据
TASKS_DIR = STORAGE_DIR / "tasks"           # 任务状态
INDEX_DIR = STORAGE_DIR / "index"           # 持久化检索索引
REPORTS_DIR = STORAGE_DIR / "reports"       # 诊断和评估报告
POINT_ANALYSIS_DIR = STORAGE_DIR / "point-analysis"  # 点位分析任务和结果

# SiliconFlow-backed RAG pipeline. Missing credentials fail closed.
SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "Qwen/Qwen3.5-9B")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "Qwen/Qwen3-Reranker-0.6B")
MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "180"))
POINT_ANALYSIS_MODEL = os.getenv("POINT_ANALYSIS_MODEL", CHAT_MODEL)
POINT_ANALYSIS_BATCH_SIZE = max(1, int(os.getenv("POINT_ANALYSIS_BATCH_SIZE", "12")))
POINT_ANALYSIS_MAX_BUNDLE_CHARS = max(10_000, int(os.getenv("POINT_ANALYSIS_MAX_BUNDLE_CHARS", "60000")))
# Legacy parser compatibility; RAG agents never use mock fallback.
ENABLE_MODEL_CALL = True
STE_URL = f"{SILICONFLOW_BASE_URL}/chat/completions"
SGE_URL = f"{SILICONFLOW_BASE_URL}/chat/completions"
STE_MODEL = CHAT_MODEL
SGE_MODEL = CHAT_MODEL

# 启动时自动创建所有目录
for _d in [ORIGINALS_DIR, PARSED_DIR, EXTRACTED_DIR, GRAPH_DIR, META_DIR, TASKS_DIR, INDEX_DIR, REPORTS_DIR, POINT_ANALYSIS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
