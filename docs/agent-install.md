# AI Agent 安装与导入（整书模式）

面向对象：使用带文件读写能力的 Agent（CodeBuddy / Claude Code / Cursor 等）的用户。
对应技能：[`skills/deep-book-reader/`](../skills/deep-book-reader/)

## 1. 安装路径一览

| 平台 | 安装路径 | 生效范围 |
| --- | --- | --- |
| CodeBuddy | `<项目>/.codebuddy/skills/deep-book-reader/` | 当前项目共享 |
| CodeBuddy | `%USERPROFILE%\.codebuddy\skills\deep-book-reader\`（macOS/Linux 为 `~/.codebuddy/skills/`） | 所有项目 |
| Claude Code | `~/.claude/skills/deep-book-reader/` | 所有项目 |
| Cursor / Windsurf / Cline 等 | 无原生 skill 机制时按第 4 节转为规则文件 | 项目或全局 |

安装动作就是把 `skills/deep-book-reader/` **整个目录**（含 `references/` 与 `scripts/`）复制过去，保持目录名不变。

```bash
# macOS / Linux
mkdir -p ~/.codebuddy/skills
cp -r skills/deep-book-reader ~/.codebuddy/skills/

# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codebuddy\skills" | Out-Null
Copy-Item -Recurse -Force "skills\deep-book-reader" "$env:USERPROFILE\.codebuddy\skills\"
```

## 2. 可选：打包成 zip 分发

若使用 CodeBuddy 的 `skill-creator` 脚本，可先校验再打包：

```bash
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/deep-book-reader
python -X utf8 <skill-creator>/scripts/package_skill.py skills/deep-book-reader ./dist
```

产出的 `dist/deep-book-reader.zip` 可直接分发给队友，解压到各自的 skills 目录即可。

> 提示：Windows 中文环境下，这两个官方脚本按系统默认编码读取 `SKILL.md`，若报 `UnicodeDecodeError`，请加 `-X utf8` 运行（如上）。

## 3. 准备书籍文本

| 来源 | 做法 |
| --- | --- |
| TXT / MD | 直接放入工作区，注意 GBK 编码书籍建议先转 UTF-8 |
| PDF（含文本层） | 用平台自带 PDF 能力，或 `pdftotext -layout book.pdf book.txt`，或 `pymupdf` |
| 扫描版 PDF | 先 OCR，再校对标点与段落边界、删除页眉页脚 |
| EPUB | 解包 XHTML，把 `h1/h2` 转成 Markdown 标题层级 |

pymupdf 示例：

```bash
python -c "import fitz,sys;d=fitz.open(sys.argv[1]);print(chr(10).join(p.get_text() for p in d))" book.pdf > book.txt
```

## 4. 无原生 skill 机制的平台：转换为规则文件

把技能内容降级为「项目规则」，效果相同，只是不会被自动触发：

1. 将 `skills/deep-book-reader/SKILL.md` 的正文（去掉 YAML frontmatter）作为主规则内容
2. 追加 `references/` 中四份文档的核心段落，或改为「需要时读取这些文件」的引用说明
3. 按平台放入对应位置：

| 平台/产品 | 放置位置 |
| --- | --- |
| 通用 Agent 约定 | 项目根 `AGENTS.md` |
| Claude Code 项目规则 | 项目根 `CLAUDE.md` |
| Cursor 规则 | `.cursor/rules/deep-book-reader.mdc` |
| ChatGPT 自定义指令/项目 | Settings → Custom instructions / Projects 文件 |
| 其他对话产品 | 会话首条消息粘贴 `SKILL.md` 正文，并按需粘贴 `references/` 内容 |

无文件读写能力的对话产品会退化为「手动粘贴章节 → 得到板块化讲解」，可用但价值有限；建议优先使用 ① NotebookLM prompt 形态。

## 5. 依赖

- **Python 3.9+**（仅用于两个脚本；不装也能用技能，只是失去切分与自动校验能力）
- 脚本仅使用标准库，无需 `pip install`
- PDF 转文本依赖平台工具或 `pymupdf` / `poppler`，与技能本身解耦

## 6. 验证安装

1. 让 Agent 列出可用技能（例如「你有哪些 skills」），确认 `deep-book-reader` 出现在列表中。
2. 直接下指令：

   ```text
   用 deep-book-reader 深度研读 work/book.pdf，生成一份完整的研读文档
   ```

3. 预期行为（对照 `SKILL.md` 工作流）：

   - Step 1：回报书名、总字数、章节数、批次计划、输出路径
   - Step 2：创建 `deep-reading/<书名>_深度研读.md` 骨架
   - Step 3：逐章追加写入板块，每章末尾带《本章总结与深度启示》
   - Step 4：末尾输出《全书宏观总结与底层知识图谱》与附录 A/B/C
   - Step 5：运行 `check_output.py` 并报告校验结果

若 Agent 直接开始写正文、没有侦察与建档动作，说明技能未被加载：检查目录名是否为 `deep-book-reader`、`SKILL.md` 是否在目录根部。

## 7. 更新与卸载

- 更新：用仓库最新版本覆盖 skills 目录下的同名目录即可（无外部依赖，无需迁移）
- 卸载：删除该技能目录
- 卸载后残留：技能运行时产生的 `deep-reading/` 目录属于你的数据，自行决定保留或删除

## 8. 排错

| 现象 | 处理 |
| --- | --- |
| 技能没被触发 | 在指令中显式点名「用 deep-book-reader 技能」 |
| 一次性读完导致后半段变摘要 | 明确要求「按 `references/long-book-strategy.md` 分批处理，逐章追加写入」 |
| 输出缺少附录/全书总结 | 要求「按 `references/output-template.md` 执行 Step 4 收尾」 |
| 出现「回复继续」等交互话术 | 说明误用了 NotebookLM 逐章 prompt，切换为整书模式 |
| `check_output.py` 报缺章节 | 用 `split_book.py` 的 `manifest.json` 核对覆盖率，补写缺失章节 |
| Python 未安装 | 跳过脚本步骤，或按平台安装 Python 3.9+ |
