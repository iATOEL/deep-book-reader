#!/usr/bin/env python3
"""校验 deep-book-reader 输出文档是否符合格式契约。

用法:
    python check_output.py "deep-reading/《书名》_深度研读.md"
    python check_output.py out.md --manifest deep-reading/_work/manifest.json

退出码: 0 = 无错误（可能有警告）；1 = 存在错误；2 = 参数或文件问题。
仅使用标准库，无第三方依赖。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover
        pass

SUMMARY_TITLE = "本章总结与深度启示"
FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
BLOCK_RE = re.compile(r"^板块\s*([0-9]+)\s*[:：]")
EXPANSION_MARK = "【扩展补充】"
CHAPTER_KEY_RE = re.compile(r"第\s*([0-9]+|[一二三四五六七八九十百零〇两]+)\s*[章节回篇讲]")
NON_CHAPTER_H2 = (
    re.compile(r"^全书导读"),
    re.compile(r"^全书宏观总结"),
    re.compile(r"^范围总结"),
    re.compile(r"^附录\s*[A-Za-zＡ-Ｚ]?"),
)
CHAPTER_H2 = re.compile(
    r"^(?:第\s*[0-9０-９一二三四五六七八九十百零〇两]+\s*[章节回篇讲]|"
    r"序章|序言|前言|导论|引言|绪论|结语|尾声|后记|跋|Chapter\s+[0-9IVXLC]+)",
    re.IGNORECASE,
)
PLACEHOLDERS = (
    "TODO", "待补充", "待完善", "TBD", "（略）", "(略)",
    "此处省略", "受篇幅限制", "不再赘述", "其余章节脉络类似", "篇幅所限",
)
INTERACTIVE = (
    '回复"继续"', "回复“继续”", "回复'继续'", "Total 章", "当前章节：", "未完成至",
)
CN_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def cn_number(token: str) -> int | None:
    if token.isdigit():
        return int(token)
    if token in CN_DIGITS:
        return CN_DIGITS[token]
    if token.startswith("十"):
        return 10 + CN_DIGITS.get(token[1:2], 0)
    if "十" in token:
        tens, ones = token.split("十", 1)
        return CN_DIGITS.get(tens, 0) * 10 + (CN_DIGITS.get(ones, 0) if ones else 0)
    return None


def strip_code_fences(lines: list[str]) -> list[tuple[int, str]]:
    """返回 (原始行号, 行内容)，跳过围栏代码块内部。"""
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((i, line))
    return out


def iter_headings(lines: list[tuple[int, str]]):
    for i, line in lines:
        m = HEADING_RE.match(line)
        if m and not line.startswith("> "):
            yield i, len(m.group(1)), m.group(2)


def count_chars(text: str) -> int:
    return len("".join(text.split()))


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def build_chapter_spans(headings, total_lines, report: Report):
    h2 = [(i, t) for i, lvl, t in headings if lvl == 2]
    chapters = []
    for pos, (line_no, title) in enumerate(h2):
        end = h2[pos + 1][0] - 1 if pos + 1 < len(h2) else total_lines - 1
        if any(rx.match(title) for rx in NON_CHAPTER_H2):
            continue
        if not CHAPTER_H2.match(title):
            report.warn(f"第 {line_no + 1} 行的 ## 标题既非章节也非白名单标题：{title}")
        chapters.append({"line": line_no, "title": title, "end": end, "h3": [], "raw": h2[pos]})
    for ch in chapters:
        ch["h3"] = [(i, t) for i, lvl, t in headings if lvl == 3 and ch["line"] < i <= ch["end"]]
    return chapters, h2


def check_structure(lines, headings, chapters, report: Report) -> None:
    h1 = [t for _, lvl, t in headings if lvl == 1]
    if len(h1) != 1:
        report.error(f"文档标题（# 级标题）应唯一，实际 {len(h1)} 个：{h1}")
    if not any(re.match(r"^全书导读", t) for _, lvl, t in headings if lvl == 2):
        report.error("缺少 ## 全书导读 章节")
    if not chapters:
        report.error("未识别到任何 ## 第 N 章 章节标题")
        return
    for ch in chapters:
        blocks = [(i, t) for i, t in ch["h3"] if BLOCK_RE.match(t)]
        summaries = [(i, t) for i, t in ch["h3"] if SUMMARY_TITLE in t]
        if not blocks:
            report.error(f"{ch['title']}：未找到任何 ### 板块 N 标题")
        numbers = [int(BLOCK_RE.match(t).group(1)) for _, t in blocks]
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            report.error(f"{ch['title']}：板块编号应为 {expected}，实际 {numbers}")
        if len(summaries) != 1:
            report.error(f"{ch['title']}：{SUMMARY_TITLE} 应恰好出现 1 次，实际 {len(summaries)} 次")
        elif summaries[0][0] < max([i for i, _ in blocks], default=-1):
            report.error(f"{ch['title']}：{SUMMARY_TITLE} 出现在部分板块之前")
        if any(ch["end"] < i for i, _ in ch["h3"]):
            report.error(f"{ch['title']}：存在超出章节范围的 ### 标题")

    last_chapter_line = chapters[-1]["line"]
    total_sections = [
        (i, t)
        for i, lvl, t in headings
        if lvl == 2 and (t.startswith("全书宏观总结") or t.startswith("范围总结"))
    ]
    if not total_sections:
        report.error("缺少 ## 全书宏观总结与底层知识图谱（或 ## 范围总结与底层逻辑）")
    elif total_sections[0][0] < last_chapter_line:
        report.error("全书总结出现在最后一章之前，位置应为全书末尾")

    meta_head = "\n".join(line for _, line in lines[:25])
    for key in ("研读范围", "来源文件"):
        if key not in meta_head:
            report.warn(f"元信息块（文档前 25 行）缺少字段：{key}")


def check_blocks(lines, chapters, report: Report, min_block_chars: int) -> tuple[list[dict], int]:
    line_map = dict(lines)
    order = [i for i, _ in lines]
    stats: list[dict] = []
    expansion_total = 0
    for ch in chapters:
        chapter_expansion = 0
        blocks = []
        body_of_chapter = 0
        for i, line in lines:
            if ch["line"] < i <= ch["end"]:
                body_of_chapter += count_chars(line)
        for pos, (start, title) in enumerate(ch["h3"]):
            end = ch["h3"][pos + 1][0] - 1 if pos + 1 < len(ch["h3"]) else ch["end"]
            body_lines = [line_map[j] for j in order if start < j <= end]
            body = "\n".join(body_lines)
            chars = count_chars(body)
            if BLOCK_RE.match(title):
                blocks.append({"title": title, "chars": chars, "start": start})
                if chars < min_block_chars:
                    report.warn(
                        f"第 {start + 1} 行 {title}：板块正文仅 {chars} 字（阈值 {min_block_chars}），疑似退化为结论罗列"
                    )
            for idx, line in enumerate(body_lines):
                stripped = line.strip()
                if stripped.startswith(">") and EXPANSION_MARK in stripped:
                    chapter_expansion += 1
                    rest = stripped.lstrip(">").replace(EXPANSION_MARK, "").strip()
                    follow = ""
                    for extra in body_lines[idx + 1 :]:
                        if extra.strip().startswith(">"):
                            follow = extra.strip().lstrip(">").strip()
                            break
                        if extra.strip():
                            break
                    if not rest and not follow:
                        report.error(f"第 {start + 1} 行附近：【扩展补充】引用块为空，应整块删除")
                    elif follow in {"无", "（无）", "(无)", "N/A"}:
                        report.error(
                            f"第 {start + 1} 行附近：【扩展补充】写成了『{follow}』，无类比时应整块删除"
                        )
        if chapter_expansion > 2:
            report.warn(f"{ch['title']}：扩展补充共 {chapter_expansion} 处，超过每章 2 处上限")
        expansion_total += chapter_expansion
        stats.append(
            {"title": ch["title"], "blocks": len(blocks), "block_chars": sum(b["chars"] for b in blocks),
             "chapter_chars": body_of_chapter, "expansion": chapter_expansion}
        )
    return stats, expansion_total


def check_forbidden(text: str, report: Report) -> None:
    for token in PLACEHOLDERS:
        if token in text:
            report.error(f"出现占位符或截断话术：{token}")
    for token in INTERACTIVE:
        if token in text:
            report.error(f"出现交互模式残留（应仅存在于 prompts/ 的逐章版本）：{token}")
    ellipsis = text.count("……")
    if ellipsis > 3:
        report.warn(f"出现 {ellipsis} 处省略号，确认不是未完成的省略内容")
    if "【原文逻辑跳跃】" in text:
        if not re.search(r"^##\s*附录[^\n]*忠实度", text, re.MULTILINE):
            report.error("存在【原文逻辑跳跃】标注，但缺少《附录 X｜忠实度与未补齐清单》")


def check_manifest(manifest_path: Path, chapters, stats, report: Report) -> None:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        report.error(f"无法读取 manifest：{exc}")
        return
    doc_titles = [ch["title"] for ch in chapters]
    doc_keys = set()
    for title in doc_titles:
        m = CHAPTER_KEY_RE.search(title)
        if m:
            num = cn_number(m.group(1))
            if num is not None:
                doc_keys.add(num)
    missing = []
    for item in manifest.get("chapters", []):
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        m = CHAPTER_KEY_RE.search(title)
        num = cn_number(m.group(1)) if m else None
        matched = (num is not None and num in doc_keys) or any(
            title.replace(" ", "") in t.replace(" ", "") or t.replace(" ", "") in title.replace(" ", "")
            for t in doc_titles
        )
        if not matched:
            missing.append(title)
    if missing:
        report.error("以下原文章节在输出文档中缺失：\n    - " + "\n    - ".join(missing))
    total_src = sum(int(c.get("chars", 0)) for c in manifest.get("chapters", []))
    total_doc = sum(s["chapter_chars"] for s in stats)
    if total_src and total_doc:
        ratio = total_doc / total_src
        print(f"[INFO] 覆盖率：原文 {total_src} 字 → 研读正文 {total_doc} 字，膨胀比 {ratio:.2f}")
        if ratio < 1.0:
            report.warn(f"膨胀比 {ratio:.2f} < 1.0，可能存在摘要化，请复核高密度理论章节")


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 deep-book-reader 输出文档")
    parser.add_argument("document", help="待校验的 Markdown 文档")
    parser.add_argument("--manifest", default=None, help="split_book.py 生成的 manifest.json（用于覆盖率校验）")
    parser.add_argument("--min-block-chars", type=int, default=80, help="板块正文最小字数（默认 80）")
    args = parser.parse_args()

    doc = Path(args.document)
    if not doc.is_file():
        print(f"[ERROR] 找不到文档: {doc}")
        return 2

    raw = doc.read_text(encoding="utf-8", errors="replace")
    is_sample = "示例输出" in raw[:400]
    text = COMMENT_RE.sub("\n", raw)
    lines_all = text.replace("\r\n", "\n").split("\n")
    lines = strip_code_fences(lines_all)
    headings = list(iter_headings(lines))

    report = Report()
    chapters, _ = build_chapter_spans(headings, len(lines_all), report)
    check_structure(lines, headings, chapters, report)
    stats, expansion_total = check_blocks(lines, chapters, report, args.min_block_chars)
    check_forbidden(text, report)
    if args.manifest:
        check_manifest(Path(args.manifest), chapters, stats, report)

    print(f"[INFO] 文档：{doc}")
    print(f"[INFO] 章节 {len(chapters)}，板块 {sum(s['blocks'] for s in stats)}，扩展补充 {expansion_total} 处")
    for item in stats:
        print(
            f"    - {item['title']}：板块 {item['blocks']}，正文 {item['chapter_chars']} 字，"
            f"扩展 {item['expansion']} 处"
        )
    if is_sample:
        print("[INFO] 检测到示例文档标记（示例输出），校验结果仅用于演示")

    for msg in report.warnings:
        print(f"[WARN] {msg}")
    for msg in report.errors:
        print(f"[ERROR] {msg}")
    if report.errors:
        print(f"[FAIL] 共 {len(report.errors)} 个错误、{len(report.warnings)} 个警告，需修正后重新校验")
        return 1
    print(f"[PASS] 无错误，{len(report.warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
