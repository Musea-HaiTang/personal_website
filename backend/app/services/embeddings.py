import hashlib

from app.config import settings


class EmbeddingError(RuntimeError):
    pass


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量生成向量；测试用 mock，真实调用只在配置 API Key 后执行。"""
    if not texts:
        return []
    if settings.embedding_mock:
        return [_mock_vector(text) for text in texts]

    api_key = settings.zai_api_key or settings.zhipu_api_key
    if not api_key:
        raise EmbeddingError("未配置 ZAI_API_KEY / ZHIPU_API_KEY")
    try:
        from zai import ZhipuAiClient

        client = ZhipuAiClient(api_key=api_key)
        response = client.embeddings.create(input=texts, model=settings.embedding_model)
    except Exception as exc:
        raise EmbeddingError(f"embedding-3 调用失败: {exc}") from exc
    data = sorted(response.data, key=lambda item: item.index or 0)
    return [item.embedding for item in data]


def _mock_vector(text: str) -> list[float]:
    digest = hashlib.sha1(text.encode("utf-8")).digest()
    return [float(digest[0] % 5), float(digest[1] % 5), float(len(text) % 7)]
