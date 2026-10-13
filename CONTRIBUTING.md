# 贡献指南

感谢参与 Deep Book Reader。本项目由两部分组成（逐章 prompt + 整书 skill），贡献时请先确认改动属于哪一部分。

## 1. 欢迎的贡献类型

| 类型 | 说明 | 主要影响文件 |
| --- | --- | --- |
| 规则改进 | 提升拆解精度、去重判据、例证取舍、模态保真等规则 | `skills/deep-book-reader/references/sifting-rules.md` + `prompts/notebooklm-configure-chat.md` |
| 输出契约改进 | 模板结构、标题契约、附录字段 | `skills/deep-book-reader/references/output-template.md` |
| 流程改进 | 分批策略、断点续写、上下文预算 | `skills/deep-book-reader/references/long-book-strategy.md` |
| 工具改进 | 切分脚本、校验脚本的参数与检查项 | `skills/deep-book-reader/scripts/*.py` |
| 文档改进 | README、docs/、示例、排错说明 | `README.md`、`docs/`、`examples/` |
| 平台适配 | 新平台的安装方式、参数建议 | `docs/agent-install.md`、`docs/platforms.md` |

新增整类的 skill 或 prompt 时，请新建目录并在 README 的目录结构与对比表中登记。

## 2. 不可妥协的原则

提交内容不得违背下列研读底线（它们是本项目的存在理由）：

1. **来源忠实**：不得向正文引入书外知识；原文缺口只能标注 `【原文逻辑跳跃】`，不得补齐。
2. **顺序保真**：不得为了「读起来更顺」而重排原书论证顺序。
3. **深度优先**：不得用「结论罗列」「概念串联单句」替代机制展开；改动时不得放宽这一条。
4. **模态保真**：弱模态（可能/似乎/倾向于）与强模态（必然/证明）不得互相改写。
5. **术语保真**：不得用自造概念替换作者术语。

如果某项改动会让上述任一规则变宽松，请在 PR 描述中明确说明理由与影响面。

## 3. 规则改动的双向同步

`prompts/notebooklm-configure-chat.md`（逐章对话形态）与 `skills/deep-book-reader/`（整书形态）共享同一套研读规则。修改规则时：

1. 先改 `skills/deep-book-reader/references/sifting-rules.md`（规则的单一事实来源）
2. 再同步修改 `prompts/notebooklm-configure-chat.md` 中对应条款（保持该文件可直接整体粘贴使用，不加 YAML frontmatter）
3. 在 PR 描述中列出两份文件的对应关系（例如「第 3 节例证极简 ↔ prompt 第 2.3 条概念去重」）
4. 形态差异（接续机制、交付方式、收尾位置）不需要也不应该同步

## 4. 脚本规范

- Python 3.9+，**仅使用标准库**，不引入第三方依赖
- 文件读写显式指定 `encoding="utf-8"`；Windows 控制台需 `sys.stdout.reconfigure(encoding="utf-8")`
- 命令行参数用 `argparse`，并提供中文 `--help` 说明
- 新增检查项时，必须在 `references/quality-gates.md` 的检查项表格中登记级别（错误/警告）
- 错误信息要能直接指导修复（说明位置 + 期望值 + 实际值）

## 5. 提交前自检

```bash
# 1. 脚本可编译
python -m py_compile skills/deep-book-reader/scripts/split_book.py skills/deep-book-reader/scripts/check_output.py

# 2. 示例输出仍能通过校验（回归测试）
python skills/deep-book-reader/scripts/check_output.py examples/output-example.md

# 3. skill 结构仍符合规范（使用 CodeBuddy 的 skill-creator 校验脚本时；中文内容需 -X utf8）
python -X utf8 <skill-creator>/scripts/quick_validate.py skills/deep-book-reader
```

若改动影响输出格式，请同步更新 `examples/output-example.md`，确保它仍是通过校验的样本。

## 6. 提交信息与 PR

提交信息建议使用 Conventional Commits：

```text
feat(skill): 增加板块正文最小字数警告
fix(script): 修复 GBK 书籍编码识别
docs(readme): 补充本地模型参数建议
```

PR 描述请包含：

- [ ] 改动属于哪一部分（prompt / skill / docs / scripts）
- [ ] 规则类改动已同步两份文件，并说明对应关系
- [ ] 已运行第 5 节的三项自检，并粘贴 `check_output.py` 的结果
- [ ] 已更新受影响的文档（README / docs / quality-gates 检查项表）
- [ ] 未引入第三方依赖，未引入受版权保护的书籍原文

## 7. 内容与法务

- 禁止提交任何受版权保护的书籍全文、长段原文引用（必要引用请控制篇幅并注明来源）
- 示例一律使用虚构文本或公有领域文本
- 新增示例书籍时，请在示例文件头部标明来源与授权情况

## 8. 行为准则

讨论保持技术化与就事论事：聚焦规则是否提升解释密度、是否越出原文边界。请勿在 issue/PR 中提交书籍资源索取请求。
