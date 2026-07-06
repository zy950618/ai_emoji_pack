# AGENTS.md — ai_emoji_pack 单用户表情包制作系统总规则

## 0. 当前项目状态

项目目标：把 `ai_emoji_pack` 重构为“表情包制作 / 提示词优化 / 质检审核 / 发布导出”的单用户 Owner 后台。

最高事实：
- 用户多次人工截图验收失败。
- 当前不能说 FINAL VERIFIED / Production Ready。
- 测试通过不等于 UI 通过。
- 人工截图反馈优先于自动评分。
- 当前必须以 `preview/golden/index.html` 作为 UI 基准。
- 当前先做 UI，再做 Prompt/SKILLS，再做 Benchmark，再做模型算法四轮提升。

## 1. 最高优先级

1. 用户最新明确指令
2. 本 `AGENTS.md`
3. `docs/00_START_HERE.md`
4. `docs/01_EXECUTION_ORDER.md`
5. `docs/02_UI_GOLDEN_PREVIEW_STANDARD.md`
6. `docs/03_PROMPT_SOURCE_INTEGRATION.md`
7. `docs/04_STICKER_SKILLS_AND_STRATEGY.md`
8. `docs/05_BENCHMARK_AND_AESTHETIC_RULES.md`
9. `docs/06_MODEL_ALGORITHM_4_PASS.md`
10. `docs/07_QUALITY_GATE_AND_TESTS.md`
11. `docs/08_CLAUDE_SUPERVISES_CODEX.md`
12. 当前真实代码

旧 LOOP、旧报告、旧截图、旧 score 只能作为失败历史，不得作为通过依据。

## 2. 绝对禁止

- 禁止说 `FINAL VERIFIED` / `Production Ready`，除非用户明确人工确认。
- 禁止把本地 PIL fallback 图当正式表情包。
- 禁止用低质圆脸、渐变背景、简单 icon 冒充候选结果。
- 禁止默认显示 `GET /api/admin`、raw enum、debug、dev_mock、英文调试文案。
- 禁止把授权放在生成主流程主视觉；授权只进入详情/发布/导出校验。
- 禁止热门样本基准作为主菜单；它应在系统设置二级配置。
- 禁止候选卡、设计资产卡片超大铺满屏幕。
- 禁止质检审核被单张大图覆盖页面。
- 禁止页面容器 id 和内部组件 id 重名。
- 禁止只改测试让它通过。
- 禁止 Claude Code 和 Codex 双方都无监督地改同一块代码。

## 3. Claude Code 与 Codex 分工

- Codex：执行代码修改、生成文件、跑测试、截图、报告。
- Claude Code：监督 Codex，不直接替 Codex 宣称完成；负责检查 diff、报告、截图、测试、规则一致性，并生成下一轮 Codex 打回指令。
- 只有用户人工确认后，才允许进入最终接收阶段。

## 4. 必须执行顺序

1. Cleanroom：删除旧规则、旧 LOOP、旧测试数据、旧 mock、旧低质 fallback 样本。
2. UI First：按 `preview/golden/index.html` 重建后台 UI。
3. SKILLS：生成表情包专用 SKILL 体系。
4. Prompt Source：接入 prompts.chat、GitHub prompt 仓库、system prompt patterns、项目内规则、Wechat-Sticker-Gen、meme-maker。
5. Benchmark：建立合法热门样本导入、风格标签、低质拒绝规则。
6. Model 4 Pass：Provider 分层、Prompt 深度、质量门禁、制作闭环。
7. Acceptance：截图、pytest、视觉验收、人工复核。

## 5. UI 尺寸门禁

- candidate-card: 220–260px，最大不得超过 280px。
- candidate-image: 180–220px，最大不得超过 240px。
- asset-card: 220–280px，最大不得超过 300px。
- asset-image: 160–200px，最大不得超过 220px。
- library thumbnail: 64–72px，最大不得超过 80px。
- detail preview: 240–300px。
- qa main preview: 300–420px，不允许单图占满屏。
- analytics chart: 260–340px。
- 1365×768 无横向溢出。
- 1920×1080 无巨大空白。

## 6. 完成声明门禁

任何一轮只能输出对应 gate：

- `CLEANROOM READY FOR USER REVIEW`
- `UI-FIRST READY FOR USER REVIEW`
- `PROMPT SOURCES READY FOR USER REVIEW`
- `BENCHMARK READY FOR USER REVIEW`
- `MODEL PASS READY FOR USER REVIEW`
- `FINAL HUMAN REVIEW REQUIRED`

不能输出最终完成类文案。
