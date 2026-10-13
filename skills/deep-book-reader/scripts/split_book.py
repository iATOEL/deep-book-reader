#!/usr/bin/env python3
"""把长篇书籍文本切分为章节文件，并生成 manifest.json 与章节骨架清单。

用法:
    python split_book.py book.txt --out deep-reading/_work --budget 40000
    python split_book.py book.md --pattern "^## 第.+章" --encoding gbk

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

DEFAULT_CHAPTER_PATTERN = (
    r"^\s*(?:#{1,6}\s+)?(?:"
    r"第\s*[0-9０-９一二三四五六七八九十百千零〇两]+\s*[章节回篇讲]"
    r"|Chapter\s+[0-9IVXLC]+"
    r"|CHAPTER\s+[0-9IVXLC]+"
    r"|(?:序章|序言|序|前言|导论|引言|绪论|结语|尾声|后记|跋|附录\s*[A-ZＡ-Ｚ]?)"
    r")"
)
MD_HEADING_RE = re.compile(r"^(#{1,4})\s+(\S.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def detect_encoding(raw: bytes) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16"
    return "utf-8"


def read_text(path: Path, encoding: str | None) -> str:
    raw = path.read_bytes()
    if encoding and encoding != "auto":
        return raw.decode(encoding, errors="replace")
    for enc in (detect_encoding(raw), "utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def strip_repeated_headers(lines: list[str], repeats: int, max_len: int) -> tuple[list[str], int]:
    """删除重复出现且较短的页眉/页脚行（默认关闭，需显式开启）。"""
    counts: dict[str, int] = {}
    for line in lines:
        s = line.strip()
        if 0 < len(s) <= max_len:
            counts[s] = counts.get(s, 0) + 1
    drop = {s for s, c in counts.items() if c >= repeats and not re.search(r"[。！？；]", s)}
    if not drop:
        return lines, 0
    kept = [ln for ln in lines if ln.strip() not in drop]
    return kept, len(drop)


def detect_md_chapters(lines: list[str]) -> list[tuple[int, str]] | None:
    levels: dict[int, list[tuple[int, str]]] = {}
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = MD_HEADING_RE.match(line)
        if m:
            levels.setdefault(len(m.group(1)), []).append((i, m.group(2).strip()))
    for lvl in sorted(levels):
        if len(levels[lvl]) >= 2:  # 取最浅的、且至少出现两次的标题层级
            return levels[lvl]
    return None


def detect_pattern_chapters(lines: list[str], pattern: str) -> list[tuple[int, str]]:
    rx = re.compile(pattern)
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if len(line) > 120:  # 过长的行几乎不会是标题行
            continue
        if rx.match(line):
            title = re.sub(r"^#{1,6}\s+", "", line.strip())
            hits.append((i, title))
    return hits


def count_chars(text: str) -> int:
    return len("".join(text.split()))


def build_chapters(
    lines: list[str], hits: list[tuple[int, str]], min_chars: int
) -> tuple[list[dict], list[str]]:
    notes: list[str] = []
    spans: list[dict] = []
    if hits and hits[0][0] > 0:
        pre_text = "\n".join(lines[: hits[0][0]]).strip()
        if count_chars(pre_text) >= min_chars:
            spans.append({"title": "前置内容（书名页/目录/序）", "start": 0, "end": hits[0][0] - 1})
    for idx, (start, title) in enumerate(hits):
        end = hits[idx + 1][0] - 1 if idx + 1 < len(hits) else len(lines) - 1
        spans.append({"title": title, "start": start, "end": end})

    chapters: list[dict] = []
    for span in spans:
        body = "\n".join(lines[span["start"] : span["end"] + 1])
        chars = count_chars(body)
        nonempty = sum(1 for ln in lines[span["start"] : span["end"] + 1] if ln.strip())
        title = span["title"]
        # 仅合并「可疑片段」：字数偏少且正文行数极少，多半是目录行或误判标题
        if chapters and chars < min_chars and (nonempty < 3 or chars < 150):
            prev = chapters[-1]
            prev["end"] = span["end"]
            prev["chars"] = count_chars("\n".join(lines[prev["start"] : prev["end"] + 1]))
            prev.setdefault("merged_titles", []).append(title)
            notes.append(f"第 {span['start'] + 1} 行附近的短片段已并入上一章节：{title}")
            continue
        chapters.append({"title": title, "start": span["start"], "end": span["end"], "chars": chars})
    return chapters, notes


def split_by_length(lines: list[str], budget: int) -> list[dict]:
    chapters: list[dict] = []
    start = 0
    buf = 0
    for i, line in enumerate(lines):
        buf += count_chars(line)
        if buf >= budget and (not line.strip() or i == len(lines) - 1):
            chapters.append(
                {"title": f"片段 {len(chapters) + 1}（按 {budget} 字自动切分）", "start": start, "end": i}
            )
            start = i + 1
            buf = 0
    if start < len(lines):
        chapters.append({"title": f"片段 {len(chapters) + 1}（按 {budget} 字自动切分）", "start": start, "end": len(lines) - 1})
    for ch in chapters:
        ch["chars"] = count_chars("\n".join(lines[ch["start"] : ch["end"] + 1]))
    return chapters


def assign_batches(chapters: list[dict], budget: int) -> list[dict]:
    batches: list[dict] = []
    current: dict | None = None
    for ch in chapters:
        if current is None or current["chars"] + ch["chars"] > budget:
            current = {"batch": len(batches) + 1, "chapters": [], "chars": 0}
            batches.append(current)
        current["chapters"].append(ch["index"])
        current["chars"] += ch["chars"]
        ch["batch"] = current["batch"]
    return batches


def safe_name(name: str, index: int) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', "_", name).strip("_")
    return f"ch{index:02d}_{cleaned[:40] or 'chapter'}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="切分长篇书籍文本并生成 manifest.json")
    parser.add_argument("book", help="书籍文本文件（txt/md）")
    parser.add_argument("--out", default="deep-reading/_work", help="输出目录（默认 deep-reading/_work）")
    parser.add_argument("--pattern", default=None, help="章节标题正则；默认自动识别中英文常见章节形式")
    parser.add_argument("--budget", type=int, default=40000, help="每批累计正文字数上限（默认 40000）")
    parser.add_argument(
        "--min-chapter-chars",
        type=int,
        default=800,
        help="低于该字数且正文行数极少的片段视为误判标题，并入上一章节（默认 800）",
    )
    parser.add_argument("--encoding", default="auto", help="输入编码，默认 auto（utf-8/gb18030 自动尝试）")
    parser.add_argument("--strip-headers", action="store_true", help="删除重复出现的短行（页眉/页脚）")
    parser.add_argument("--header-repeats", type=int, default=8, help="判定页眉页脚的重复次数阈值（默认 8）")
    args = parser.parse_args()

    src = Path(args.book)
    if not src.is_file():
        print(f"[ERROR] 找不到输入文件: {src}")
        return 2

    text = read_text(src, args.encoding)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    if args.strip_headers:
        lines, dropped = strip_repeated_headers(lines, args.header_repeats, 60)
        if dropped:
            print(f"[INFO] 已删除 {dropped} 类重复的短行（页眉/页脚候选）")

    md_hits = detect_md_chapters(lines)
    split_mode = "md-headings"
    hits = md_hits or []
    if not md_hits:
        split_mode = "pattern"
        hits = detect_pattern_chapters(lines, args.pattern or DEFAULT_CHAPTER_PATTERN)
    if len(hits) < 2:
        print("[WARN] 未识别到足够章节标题，退化为按字数切分；请用 --pattern 指定章节标题正则。")
        split_mode = "by-length"
        chapters = split_by_length(lines, args.budget)
        notes: list[str] = []
    else:
        chapters, notes = build_chapters(lines, hits, args.min_chapter_chars)

    for i, ch in enumerate(chapters, start=1):
        ch["index"] = i

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for ch in chapters:
        body = "\n".join(lines[ch["start"] : ch["end"] + 1]).strip() + "\n"
        filename = safe_name(ch["title"], ch["index"])
        (out_dir / filename).write_text(body, encoding="utf-8")
        ch["file"] = filename
        ch["start_line"] = ch["start"] + 1
        ch["end_line"] = ch["end"] + 1
        ch.pop("start", None)
        ch.pop("end", None)

    batches = assign_batches(chapters, args.budget)
    manifest = {
        "source": str(src),
        "split_mode": split_mode,
        "total_chars": count_chars(text),
        "chapter_count": len(chapters),
        "batch_count": len(batches),
        "budget_per_batch": args.budget,
        "chapters": chapters,
        "batches": batches,
        "notes": notes,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    skeleton = ["# 章节骨架清单", "", f"来源：{src}", f"总字数：{manifest['total_chars']}", ""]
    skeleton.append("| 序号 | 建议批次 | 章节标题 | 字数 | 文件 |")
    skeleton.append("| --- | --- | --- | --- | --- |")
    for ch in chapters:
        skeleton.append(
            f"| {ch['index']} | {ch.get('batch')} | {ch['title']} | {ch['chars']} | {ch['file']} |"
        )
    if notes:
        skeleton += ["", "## 处理提示", ""] + [f"- {n}" for n in notes]
    (out_dir / "_骨架.md").write_text("\n".join(skeleton) + "\n", encoding="utf-8")

    print(f"[OK] 切分模式: {split_mode}")
    print(f"[OK] 总字数 {manifest['total_chars']}，章节 {len(chapters)}，批次 {len(batches)}")
    for batch in batches:
        titles = "；".join(chapters[i - 1]["title"] for i in batch["chapters"][:4])
        more = " 等" if len(batch["chapters"]) > 4 else ""
        print(f"  批次 {batch['batch']}：{batch['chars']} 字 → {titles}{more}")
    print(f"[OK] 输出目录: {out_dir.resolve()}")
    print(f"[OK] 清单文件: {(out_dir / 'manifest.json').resolve()}")
    print(f"[OK] 章节骨架: {(out_dir / '_骨架.md').resolve()}")
    for note in notes:
        print(f"[WARN] {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
