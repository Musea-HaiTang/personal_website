import json
import re

from sqlalchemy import select
import yaml

from app.models.quiz import Question

QUIZ_TEMPLATE = """# 技术答题题库格式文档（给 AI 生成题目时参考）
# 必填：category、questions[].type、title；choice 必填 options（固定 4 项 A-D）与 answer（填 A/B/C/D）；fill 必填 code/answer
# 注意：题号键必须写成 "no":，加引号，否则 YAML 会把 no 解析成布尔值
# 分类固定写在文件顶部，整个文件一个分类；一次可导入多题

# 分类固定写在文件顶部，整个文件一个分类
category: Python
questions:
  - type: choice          # choice=选择题（考概念）
    "no": "1.1"           # 题号，可选；键必须加引号；留空自动编号
    score: 5              # 分值，可选；默认 choice=5、fill=10
    title: 下面哪个是 Python 装饰器的正确理解？
    options:              # 固定 4 项，从左到右对应 A/B/C/D
      - 装饰器是接收函数并返回新函数的可调用对象   # A
      - 装饰器只能修饰类方法                      # B
      - 被 @ 装饰的函数会立即执行                 # C
      - 装饰器是 Python 3 才有的特性              # D
    answer: A             # 正确选项的字母，只能填 A/B/C/D 之一
    explanation: |
      装饰器本质是接收函数并返回新函数的可调用对象。

  - type: fill            # fill=填空题（考代码挖空）
    "no": "1.2"
    score: 10
    title: 补全装饰器：返回内部函数
    code: |
      def timer(fn):
          def wrap(*a, **kw):
              return fn(*a, **kw)
          return ____
    answer: wrap           # 标准答案
    accept:                # 可选：其他可接受答案
      - wrap
    explanation: |
      装饰器要把 wrap 返回出去替换原函数。
"""

_LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}


def parse_quiz_yaml(text: str) -> tuple[str, list[dict], list[str]]:
    """解析并校验题库 YAML，返回 (category, 规范化题目列表, 错误列表)。"""
    errors: list[str] = []
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return "", [], [f"YAML 解析失败：{exc}"]

    if not isinstance(data, dict) or not isinstance(data.get("category"), str) or not data["category"].strip():
        errors.append("缺少文件级 category（写在文件顶部）")
        return "", [], errors
    category = data["category"].strip()

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("questions 为空或格式不正确（应为列表）")
        return category, [], errors

    items: list[dict] = []
    for i, raw in enumerate(questions, start=1):
        if not isinstance(raw, dict):
            errors.append(f"第 {i} 题：格式不是对象")
            continue
        label = f"第 {i} 题（{raw.get('title', '无标题')}）"
        qtype = raw.get("type")
        if qtype not in ("choice", "fill"):
            errors.append(f"{label}：type 只能是 choice 或 fill")
            continue
        title = str(raw.get("title") or "").strip()
        if not title:
            errors.append(f"{label}：缺少 title")
            continue

        score_raw = raw.get("score")
        try:
            score = int(score_raw) if score_raw is not None else (5 if qtype == "choice" else 10)
        except (TypeError, ValueError):
            errors.append(f"{label}：score 必须是整数")
            continue
        if score < 1:
            errors.append(f"{label}：score 必须大于 0")
            continue

        no = str(raw.get("no") or raw.get(False) or "").strip()
        explanation = str(raw.get("explanation") or "").strip()
        answer = ""
        options: list[str] = []
        code: str | None = None

        if qtype == "choice":
            options = [str(o).strip() for o in (raw.get("options") or [])]
            if len(options) != 4 or any(not o for o in options):
                errors.append(f"{label}：选择题 options 必须固定 4 项")
                continue
            letter = str(raw.get("answer") or "").strip().upper()
            if letter not in _LETTER_TO_INDEX:
                errors.append(f"{label}：answer 只能填 A/B/C/D 之一")
                continue
            answer = letter
        else:
            code = str(raw.get("code") or "")
            if "____" not in code:
                errors.append(f"{label}：填空题 code 必须包含 ____ 空位")
                continue
            answer = str(raw.get("answer") or "").strip()
            if not answer:
                errors.append(f"{label}：填空题缺少 answer")
                continue
        accept = [str(a).strip() for a in (raw.get("accept") or []) if str(a).strip()]

        items.append(
            {
                "category": category,
                "no": no,
                "type": qtype,
                "title": title,
                "options": options,
                "accept": accept,
                "answer": answer,
                "code": code,
                "reference_answer": str(raw.get("reference_answer") or "").strip() or None,
                "explanation": explanation,
                "score": score,
            }
        )
    return category, items, errors


def _item_key(item: dict) -> tuple[str, str]:
    """同分类同题号视为同一题；题号为空时按标题判断。"""
    return (item["category"], item["no"] or item["title"])


def _existing_map(db) -> dict[tuple[str, str], Question]:
    return {(q.category, q.no or q.title): q for q in db.scalars(select(Question)).all()}


def preview_import(items: list[dict], db) -> tuple[list[str], list[str]]:
    """对照数据库，返回 (新增标题列表, 更新标题列表)。"""
    existing = _existing_map(db)
    new, updated = [], []
    for item in items:
        key = _item_key(item)
        if key in existing:
            updated.append(item["title"])
        else:
            new.append(item["title"])
    return new, updated


def apply_import(items: list[dict], db) -> tuple[int, int]:
    """写入题目：同 key 更新，否则新增。返回 (新增数, 更新数)。"""
    existing = _existing_map(db)

    imported, updated = 0, 0
    for item in items:
        key = _item_key(item)
        question = existing.get(key)
        if question is None:
            question = Question(category=item["category"], no=item["no"], type=item["type"], title=item["title"])
            db.add(question)
            imported += 1
        else:
            updated += 1
        question.type = item["type"]
        question.title = item["title"]
        question.options = json.dumps(item["options"], ensure_ascii=False)
        question.accept = json.dumps(item["accept"], ensure_ascii=False)
        question.answer = item["answer"]
        question.code = item["code"]
        question.reference_answer = item["reference_answer"]
        question.explanation = item["explanation"]
        question.score = item["score"]
    db.commit()
    return imported, updated
