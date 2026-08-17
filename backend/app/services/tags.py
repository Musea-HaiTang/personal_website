"""标签序列化：数据库存逗号分隔字符串，接口层用列表。"""


def to_str(tags: list[str]) -> str:
    return ",".join(tag.strip() for tag in tags if tag.strip())


def to_list(tags_str: str) -> list[str]:
    return [tag for tag in (tags_str or "").split(",") if tag.strip()]
