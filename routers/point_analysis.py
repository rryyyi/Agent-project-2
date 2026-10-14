"""点位重要性分析 API。"""

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import PurePosixPath, PureWindowsPath

import aiofiles
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from config import POINT_ANALYSIS_DIR
from services import point_analysis_service as analysis

router = APIRouter(prefix="/api/v1/point-analysis", tags=["point-analysis"])

MAX_FILES = 1_000
MAX_TOTAL_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def _safe_run_id(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError) as exc:
        raise HTTPException(404, "分析任务不存在") from exc


def _relative_upload_path(filename: str | None) -> PurePosixPath:
    raw = (filename or "").replace("\\", "/")
    windows_path = PureWindowsPath(raw)
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise HTTPException(400, "上传文件包含无效路径")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise HTTPException(400, "上传文件包含无效路径")
    safe_parts = [re.sub(r'[<>:"|?*\x00-\x1f]', "_", part).rstrip(" .") for part in path.parts]
    if any(not part for part in safe_parts):
        raise HTTPException(400, "上传文件名无效")
    return PurePosixPath(*safe_parts)


@router.post("/runs", status_code=202)
async def create_point_analysis(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="点位表和 PLC 工程文件，可多选或上传目录"),
):
    if not files:
        raise HTTPException(400, "请至少选择一个点位表或工业工程文件")
    if len(files) > MAX_FILES:
        raise HTTPException(413, f"单次最多上传 {MAX_FILES} 个文件")

    run_id = str(uuid.uuid4())
    run_dir = POINT_ANALYSIS_DIR / run_id
    input_dir = run_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    filenames: list[str] = []
    total_size = 0
    try:
        for upload in files:
            relative = _relative_upload_path(upload.filename)
            relative_name = relative.as_posix()
            if relative_name.casefold() in seen:
                raise HTTPException(400, f"上传文件路径重复: {relative_name}")
            seen.add(relative_name.casefold())
            destination = input_dir.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            file_size = 0
            async with aiofiles.open(destination, "wb") as output:
                while chunk := await upload.read(CHUNK_SIZE):
                    file_size += len(chunk)
                    total_size += len(chunk)
                    if total_size > MAX_TOTAL_UPLOAD_BYTES:
                        raise HTTPException(413, "单次上传总大小不能超过 2 GB")
                    await output.write(chunk)
            if file_size == 0:
                raise HTTPException(400, f"上传文件为空: {relative_name}")
            filenames.append(relative_name)
            await upload.close()

        if not any(name.lower().endswith(".csv") for name in filenames):
            raise HTTPException(400, "请同时上传包含 Device、Name、Address、Type 四列的 CSV 点位表")
        run = analysis.create_run(run_id, str(input_dir), filenames)
        background_tasks.add_task(analysis.run_analysis, run_id, str(input_dir))
        return run
    except Exception:
        shutil.rmtree(run_dir, ignore_errors=True)
        raise


@router.get("/runs/{run_id}")
async def get_point_analysis_status(run_id: str):
    run_id = _safe_run_id(run_id)
    run = analysis.load_run(run_id)
    if not run:
        raise HTTPException(404, "分析任务不存在")
    return run


@router.get("/runs/{run_id}/results")
async def get_point_analysis_results(
    run_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    search: str | None = Query(None, max_length=200),
):
    run_id = _safe_run_id(run_id)
    run = analysis.load_run(run_id)
    if not run:
        raise HTTPException(404, "分析任务不存在")
    if run.get("status") != "completed":
        raise HTTPException(409, "分析尚未完成")
    report = analysis.load_results(run_id)
    if not report:
        raise HTTPException(404, "分析结果不存在")

    rows = report.get("rows", [])
    if status:
        rows = [row for row in rows if row.get("验证状态") == status]
    if search:
        needle = search.casefold()
        fields = ("Device", "Name", "Address", "Type", "重要性等级", "验证状态", "验证结论", "证据定位")
        rows = [row for row in rows if any(needle in str(row.get(field, "")).casefold() for field in fields)]
    total = len(rows)
    start = (page - 1) * page_size
    return {
        "run_id": run_id,
        "summary": report.get("summary", {}),
        "page": page,
        "page_size": page_size,
        "total": total,
        "rows": rows[start:start + page_size],
        "warnings": run.get("warnings", []),
    }


@router.get("/runs/{run_id}/download")
async def download_point_analysis_csv(run_id: str):
    run_id = _safe_run_id(run_id)
    run = analysis.load_run(run_id)
    if not run:
        raise HTTPException(404, "分析任务不存在")
    if run.get("status") != "completed":
        raise HTTPException(409, "分析尚未完成")
    path = analysis.run_path(run_id) / "关键点位分析.csv"
    if not path.is_file():
        raise HTTPException(404, "CSV 结果不存在")
    return FileResponse(path, media_type="text/csv; charset=utf-8", filename="关键点位分析.csv")
