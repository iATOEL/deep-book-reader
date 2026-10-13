# 输入示例

本节给出四类输入：Agent 自然语言指令、带参数的指令模板、NotebookLM 对话输入、脚本命令。

示例书为 [`examples/sample-book.md`](sample-book.md)（**虚构**示例书，891 字正文，2 章），其生成的研读文档见 [`examples/output-example.md`](output-example.md)。

## 1. Agent 自然语言指令（最常用）

```text
用 deep-book-reader 深度研读 work/《概念与范畴》.pdf，生成一份完整的研读文档
```

```text
按 deep-book-reader 的规则，把这本书拆成板块讲透，输出到 deep-reading/ 下，我需要一份可归档的整书研读文档
```

```text
用 deep-book-reader 处理这本书，只做第 3–5 章，术语保留英文原词
```

Agent 收到指令后的预期动作（对照 `skills/deep-book-reader/SKILL.md`）：

1. 回报侦察结论：书名、总字数、章节数、批次计划、输出路径
2. 建立文档骨架（元信息块 + 全书导读 + 各章标题）
3. 逐章完整读取原文 → 划分板块 → 展开机制 → 写入 `### 本章总结与深度启示` → 追加写入文件
4. 收尾追加《全书宏观总结与底层知识图谱》与附录 A/B/C
5. 运行 `check_output.py`，报告校验结果与膨胀比

## 2. 带参数的指令模板（可复制）

```text
用 deep-book-reader 研读这本书，参数如下：
- 书籍：work/book.pdf
- 章节范围：全书
- 输出路径：deep-reading/《书名》_深度研读.md
- 读者背景：哲学专业本科生（非计量经济学方向）
- 类比扩展：允许，每章最多 1 处
- 输出语言：中文，专业术语保留英文原词
- 批次预算：30000 字/批（我的模型上下文 64k）

要求：按 SKILL.md 的 Step 1–5 执行，逐章追加写入，最后运行 check_output.py 并报告结果。
```

## 3. NotebookLM 对话输入（逐章模式）

先在 Configure chat 中粘贴 [`prompts/notebooklm-configure-chat.md`](../prompts/notebooklm-configure-chat.md) 全文，然后在对话中：

```text
开始讲解
```

```text
讲解第 5 章
```

```text
继续
```

预期输出片段（章首）：

```text
当前章节：[第 1 章 / 共 12 章：从计数到记数]
核心主旨：[本章区分计数与记数两种活动，指出记数的第一要求是可复现。]

---

### 板块 1：计数与记数的分野
...
```

## 4. 脚本命令与真实输出

### 4.1 切分长书并生成批次计划

```bash
python skills/deep-book-reader/scripts/split_book.py examples/sample-book.md --out deep-reading/_work
```

对示例书的真实输出：

```text
[OK] 切分模式: md-headings
[OK] 总字数 965，章节 2，批次 1
  批次 1：891 字 → 第 1 章 从"数出来"到"写下来"；第 2 章 位值制的代价

[OK] 输出目录: F:\Tool\Paper\deep-reading\_work
[OK] 清单文件: F:\Tool\Paper\deep-reading\_work\manifest.json
[OK] 章节骨架: F:\Tool\Paper\deep-reading\_work\_骨架.md
```

常用参数：

```bash
# 模型上下文较小：每批 15000 字
python skills/deep-book-reader/scripts/split_book.py work/book.txt --out deep-reading/_work --budget 15000

# 电子书章节标题不规范：自定义正则
python skills/deep-book-reader/scripts/split_book.py work/book.txt --pattern "^第[0-9]+讲"

# GBK 编码的 TXT，并删除重复页眉页脚
python skills/deep-book-reader/scripts/split_book.py work/book.txt --encoding gbk --strip-headers
```

`manifest.json` 片段（真实输出）：

```json
{
  "split_mode": "md-headings",
  "total_chars": 965,
  "chapter_count": 2,
  "batch_count": 1,
  "chapters": [
    {"title": "第 1 章 从\"数出来\"到\"写下来\"", "chars": 580, "index": 1, "file": "ch01_第_1_章_从_数出来_到_写下来.md", "start_line": 5, "end_line": 18, "batch": 1},
    {"title": "第 2 章 位值制的代价", "chars": 311, "index": 2, "file": "ch02_第_2_章_位值制的代价.md", "start_line": 19, "end_line": 26, "batch": 1}
  ]
}
```

### 4.2 校验输出文档

```bash
python skills/deep-book-reader/scripts/check_output.py examples/output-example.md --manifest deep-reading/_work/manifest.json
```

真实输出：

```text
[INFO] 覆盖率：原文 891 字 → 研读正文 3324 字，膨胀比 3.73
[INFO] 文档：examples\output-example.md
[INFO] 章节 2，板块 7，扩展补充 1 处
    - 第 1 章 从"数出来"到"写下来"：板块 4，正文 2052 字，扩展 1 处
    - 第 2 章 位值制的代价：板块 3，正文 1272 字，扩展 0 处
[INFO] 检测到示例文档标记（示例输出），校验结果仅用于演示
[PASS] 无错误，0 个警告
```

存在错误时（示例）：

```text
[ERROR] 第 2 章 位值制的代价：板块编号应为 [1, 2, 3]，实际 [1, 3]
[ERROR] 出现占位符或截断话术：待补充
[WARN] 第 88 行 板块 2：板块正文仅 46 字（阈值 80），疑似退化为结论罗列
[FAIL] 共 2 个错误、1 个警告，需修正后重新校验
```

## 5. 输入文件要求

| 项目 | 要求 |
| --- | --- |
| 格式 | TXT / MD 最佳；PDF 建议先转文本；EPUB 先解包转 Markdown |
| 编码 | UTF-8 优先；GBK 书籍用 `--encoding gbk` 或先转码 |
| 章节标题 | 越规范越好（`第 N 章`、`Chapter N`、Markdown 标题）；不规范时用 `--pattern` 指定 |
| 目录 | 电子书目录页会被识别为"前置内容"，不影响章节定位；必要时手动删除 |
| 篇幅 | 无上限；超过 8 万字或 12 章时按 `references/long-book-strategy.md` 分批 |
| 版权 | 仅处理你拥有合法使用权的内容；示例一律使用虚构或公有领域文本 |
