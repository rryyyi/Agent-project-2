"""SiliconFlow OpenAI-compatible client. Every RAG operation is fail-closed."""
import json
import re
import asyncio
import httpx

from config import (SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, CHAT_MODEL,
                    EMBEDDING_MODEL, RERANKER_MODEL, MODEL_TIMEOUT)


class ModelServiceError(RuntimeError):
    pass


def _headers():
    if not SILICONFLOW_API_KEY:
        raise ModelServiceError("SILICONFLOW_API_KEY 未配置")
    return {"Authorization": f"Bearer {SILICONFLOW_API_KEY}", "Content-Type": "application/json"}


async def chat(messages: list[dict], *, json_mode: bool = False, max_tokens: int = 1800,
               model: str | None = None) -> str:
    body = {"model": model or CHAT_MODEL, "messages": messages, "temperature": 0.1, "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    response = await _post_with_retry("/chat/completions", body)
    if response.status_code >= 400:
        raise ModelServiceError(f"chat HTTP {response.status_code}: {response.text[:500]}")
    try:
        return response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelServiceError("chat 响应格式无效") from exc


async def embeddings(texts: list[str]) -> list[list[float]]:
    response = await _post_with_retry("/embeddings", {"model": EMBEDDING_MODEL, "input": texts})
    if response.status_code >= 400:
        raise ModelServiceError(f"embedding HTTP {response.status_code}: {response.text[:500]}")
    data = response.json().get("data", [])
    if len(data) != len(texts):
        raise ModelServiceError("embedding 数量与输入不一致")
    return [x["embedding"] for x in sorted(data, key=lambda x: x.get("index", 0))]


async def rerank(query: str, documents: list[str]) -> list[float]:
    if not documents:
        return []
    response = await _post_with_retry("/rerank", {"model": RERANKER_MODEL, "query": query,
                                                   "documents": documents, "top_n": len(documents),
                                                   "return_documents": False})
    if response.status_code >= 400:
        raise ModelServiceError(f"rerank HTTP {response.status_code}: {response.text[:500]}")
    scores = [0.0] * len(documents)
    for item in response.json().get("results", []):
        scores[item.get("index", 0)] = float(item.get("relevance_score", 0))
    return scores


async def _post_with_retry(path: str, body: dict) -> httpx.Response:
    """Retry transient transport failures only; never substitute a local/mock result."""
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=MODEL_TIMEOUT, http2=False,
                                         limits=httpx.Limits(max_keepalive_connections=2)) as client:
                return await client.post(f"{SILICONFLOW_BASE_URL}{path}", headers=_headers(), json=body)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))
    raise ModelServiceError(f"SiliconFlow transport failed after retries: {last_error}")


def parse_json_object(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            raise ModelServiceError("模型没有返回合法 JSON")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ModelServiceError("模型 JSON 无法解析") from exc
