# Deep Book Reader｜整书深度研读

**同一套研读哲学，两种交付形态。**

把一本书变成「真正讲透」的文档，而不是一段摘要。本项目把「来源忠实、机制展开、去重精炼、模态保真」的研读规则固化成可复用的资产，同时服务两类用户：

| 形态 | 面向对象 | 交付结果 | 入口文件 |
| --- | --- | --- | --- |
| **① NotebookLM Prompt** | 用 NotebookLM 上传 PDF 读书的用户 | 对话式，一章一章讲，回复「继续」接续 | `prompts/notebooklm-configure-chat.md` |
| **② AI Agent Skill** | 用 CodeBuddy / Claude Code / Cursor 等带文件读写能力的 Agent 用户 | **一次运行产出一份完整 Markdown 研读文档**，整本书一次讲完 | `skills/deep-book-reader/` |

两条路径共享同一套深度规则：**不引入书外知识、不补齐原文缺口、不做结论罗列、不改变论证顺序、不篡改原文模态强度。**

---

## 它解决什么问题

直接用通用 AI 做读书笔记，常见四类劣化：

| 劣化 | 表现 | 本项目的对策 |
| --- | --- | --- |
| 摘要化 | 一章被压成三句结论 | 解释密度规则 + 复杂度阈值 + 段落级机制展开 |
| 幻觉补齐 | 用模型常识补上原文没写的推导 | 来源忠实与防补齐，缺口处标注 `【原文逻辑跳跃】` |
| 顺序错乱 | 按模型偏好重排论证 | 逻辑与顺序保真，板块编号与章节顺序受脚本校验 |
| 强度改写 | 「可能」被写成「必然」 | 论证强度保真表（弱模态/强模态对照） |

---

## 目录结构

```text
.
├── README.md                             # 本文件：总览、快速开始、对比与导航
├── LICENSE                               # MIT 许可证
├── CONTRIBUTING.md                       # 贡献指南与校验要求
├── prompts/
│   └── notebooklm-configure-chat.md      # ① NotebookLM「Configure chat」prompt（逐章模式，原样可粘贴）
├── skills/
│   └── deep-book-reader/                 # ② AI Agent 技能（整书模式）
│       ├── SKILL.md                      #    技能说明、工作流 Step 1–5、硬性约束
│       ├── references/
│       │   ├── output-template.md        #    输出文档模板与格式契约
│       │   ├── sifting-rules.md          #    板块划分、解释密度、例证极简、防越界细则
│       │   ├── long-book-strategy.md     #    长书分批、断点续写、异常处理
│       │   └── quality-gates.md          #    交付前自检清单与常见报错修复
│       └── scripts/
│           ├── split_book.py             #    长书切分 + 生成 manifest.json（标准库，无依赖）
│           └── check_output.py           #    输出文档结构/格式/覆盖率校验
├── docs/
│   ├── notebooklm-setup.md               # 如何把 prompt 用于 NotebookLM（含排错）
│   ├── agent-install.md                  # 各平台技能安装/导入方式
│   ├── use-cases.md                      # 使用场景与推荐配置
│   └── platforms.md                       # 适用模型/平台与参数建议
└── examples/
    ├── sample-book.md                    # 虚构示例书（891 字，2 章），输入输出示例的共同基准
    ├── input-example.md                  # 输入示例：调用语句、参数模板、脚本命令与真实输出
    └── output-example.md                 # 输出示例：完整研读文档（可通过 check_output.py）
```

---

## 快速开始

### A. NotebookLM 用户（3 步）

1. 新建 Notebook，上传书籍 PDF（**一个 Notebook 只放一本书**，避免来源串味）。
2. 打开 **Configure chat**，把 `prompts/notebooklm-configure-chat.md` 全文粘贴进去并保存。
3. 新开一条对话，输入「开始讲解」即可。后续：

   - 想看下一章 → 回复「继续」
   - 想指定章节 → 「讲解第 5 章」
   - 单章没讲完 → 按提示回复「继续」，从下一个板块接着讲

  详细步骤与排错见 [`docs/notebooklm-setup.md`](docs/notebooklm-setup.md)。

### B. AI Agent 用户（3 步）

1. 安装技能：把 `skills/deep-book-reader/` 整个目录复制到 Agent 的 skills 目录

   ```bash
   # CodeBuddy（用户级，所有项目可用）
   # Windows: %USERPROFILE%\.codebuddy\skills\deep-book-reader
   # macOS/Linux: ~/.codebuddy/skills/deep-book-reader

   # 或项目级：<项目>/.codebuddy/skills/deep-book-reader
   ```

2. 把书放进工作区（PDF 先转文本，见 [`docs/agent-install.md`](docs/agent-install.md)）。
3. 对 Agent 说：

   ```text
   用 deep-book-reader 深度研读 work/book.pdf，生成一份完整的研读文档
   ```

   Agent 会按 `SKILL.md` 的 Step 1–5 执行：侦察建档 → 建骨架 → 逐章展开并追加写入 → 全书收尾 → 校验交付，最终产出 `deep-reading/<书名>_深度研读.md`。

---

## 输入输出示例

- 输入示例：[`examples/input-example.md`](examples/input-example.md)（自然语言调用、参数模板、脚本命令、示例书原文节选）
- 输出示例：[`examples/output-example.md`](examples/output-example.md)（对示例书生成的完整研读文档）

示例输出是可复现的校验样本：

```bash
python skills/deep-book-reader/scripts/check_output.py examples/output-example.md
# [PASS] 无错误
```

输出文档骨架：

```markdown
# 《书名》深度研读
> 研读范围 / 来源文件 / 原文规模 / 生成时间 / 生成方式
## 全书导读（核心论题 · 论证主线骨架 · 使用约定）
## 第 1 章 <章节名>
### 板块 1：<核心子主题>      ← 机制展开正文
> 【扩展补充】               ← 至多 1 个通俗类比，无则整块删除
### 本章总结与深度启示        ← 核心逻辑链条 + 关键启示
## 第 2 章 …
## 全书宏观总结与底层知识图谱
## 附录 A｜术语表 · 附录 B｜忠实度与未补齐清单 · 附录 C｜覆盖率与批次记录
```

---

## 两种形态对比

| 维度 | ① NotebookLM Prompt | ② AI Agent Skill |
| --- | --- | --- |
| 交互方式 | 多轮对话，一次一章 | 一句话触发，全程自动 |
| 接续机制 | 用户回复「继续」 | 内部批次 + 断点续写 |
| 交付物 | 对话记录 | 单个 Markdown 文件 |
| 篇幅上限 | 受单次回复长度限制 | 不受限，按章追加写入 |
| 全书收尾 | 讲到最后一章时的对话输出 | 文档末尾《全书宏观总结与底层知识图谱》+ 附录 |
| 可校验性 | 靠人工对照 prompt | `check_output.py` 结构/格式/覆盖率校验 |
| 适合场景 | 想边读边问、随时追问 | 想一次性拿到可归档的整书文档 |

---

## 使用场景

| 场景 | 推荐形态 | 说明 |
| --- | --- | --- |
| 学术专著精读、理论书拆解 | ② Agent Skill | 需要完整机制链条与可检索文档 |
| 边读边问、逐章讨论 | ① NotebookLM Prompt | 交互式陪读，强调即时追问 |
| 论文/长报告深读 | ② Agent Skill | 结构同构，按章节拆解即可 |
| 读书会底稿、团队共读材料 | ② Agent Skill | 输出单文件便于分发与批注 |
| 备考与知识体系搭建 | ② Agent Skill | 附录 A 术语表 + 全书知识图谱 |
| 轻小说、散文随笔、操作手册 | 不建议 | 缺少推导链条，规则会显得过重 |

完整场景与推荐参数见 [`docs/use-cases.md`](docs/use-cases.md)。

---

## 适用模型与平台

| 平台/模型 | 支持方式 | 备注 |
| --- | --- | --- |
| NotebookLM（Gemini） | 用 ① prompt | 原生来源引用，适合 PDF 阅读 |
| CodeBuddy | 用 ② skill（原生 `SKILL.md` 机制） | 项目级 `.codebuddy/skills/`、用户级 `~/.codebuddy/skills/` |
| Claude Code / Claude 系列 | 用 ② skill（`~/.claude/skills/`） | 长上下文 + 文件读写，效果稳定 |
| Cursor / Windsurf / Cline 等 IDE Agent | 用 ② skill（转为项目规则或技能目录） | 无原生 skill 机制时，把 `SKILL.md` 与 `references/` 作为规则文件 |
| ChatGPT / 通用对话产品 | 用 ② 内容作为自定义指令或项目规则 | 无文件读写时需手动粘贴章节，效果受限 |
| 本地模型（Qwen / GLM / Llama 等） | 用 ② skill，配合小批次参数 | 上下文不足会导致摘要化，务必跑校验脚本 |

能力要求与参数建议见 [`docs/platforms.md`](docs/platforms.md)。

---

## 常见问题

**Q：两条路径的内容会重复维护吗？**
不会。① 是逐章对话形态的 prompt，② 是整书交付形态的 skill。研读规则在 `skills/deep-book-reader/references/sifting-rules.md` 中集中维护，修改规则时同步检查 prompt 中的对应条款（见 `CONTRIBUTING.md`）。

**Q：书籍版权怎么处理？**
本项目只提供方法、模板与脚本，不包含任何受版权保护的书籍全文。示例使用虚构文本。使用者需自行确保对所用书籍拥有合法使用权。

**Q：能处理几十万字的书吗？**
可以。`split_book.py` 按章节切分并给出批次计划，`long-book-strategy.md` 规定断点续写与上下文预算；关键是**按章追加写入**，而不是一次读完整本。

**Q：PDF 扫描件怎么办？**
先 OCR 再校对标点与段落边界；转换注意事项见 `references/long-book-strategy.md` 第 2 节。

**Q：输出太长/太短怎么办？**
长度由逻辑节点与推导复杂度决定。若明显偏短，用 `check_output.py` 看膨胀比；低于 1.0 的高密度理论章节通常意味着发生了摘要化。

---

## 发布到 GitHub

```bash
git init
git add .
git commit -m "feat: 初始化 deep-book-reader（NotebookLM prompt + AI Agent skill）"
git branch -M main
git remote add origin https://github.com/<你的账号>/deep-book-reader.git
git push -u origin main
```

仓库根目录已完成 GitHub 就绪配置：`README.md`、`LICENSE`、`CONTRIBUTING.md`、`.gitignore`。

---

## 许可证与贡献

- 许可证：[MIT](LICENSE)
- 贡献指南：[`CONTRIBUTING.md`](CONTRIBUTING.md)（含改动规则时的自检要求与 PR 清单）

---

## English

**Deep Book Reader** packages one deep-reading methodology into two deliverables:

- `prompts/notebooklm-configure-chat.md` — a NotebookLM "Configure chat" prompt that explains an uploaded book **chapter by chapter**, resuming when you reply "continue".
- `skills/deep-book-reader/` — an AI-agent skill that produces **one complete Markdown study document for the whole book** in a single run (chapter → logical blocks → mechanism-level explanation), with bundled Python scripts for chapter splitting and output validation.

Both share the same rules: source fidelity (never fill in gaps the author left out — mark them as `【原文逻辑跳跃】`), argument-order fidelity, mechanism-level depth instead of summary, example minimalism, and modality preservation. Install by copying the skill folder into your agent's skills directory, then say: *"Use deep-book-reader to deeply analyze this book and generate the full study document."* MIT licensed.
