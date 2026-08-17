"""搜索接缝：先提供内存关键词匹配；P1 向量检索在此替换实现，调用方不变。"""


def matches(haystacks: list[str | None], keyword: str | None) -> bool:
    """关键词是否命中任一字段（大小写不敏感）；关键词为空视为全命中。"""
    kw = (keyword or "").strip().lower()
    if not kw:
        return True
    return any(kw in (s or "").lower() for s in haystacks)
