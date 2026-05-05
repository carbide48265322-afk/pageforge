# PageForge — Prompt 系统改进计划

> **状态:** 📋 待执行
> **创建日期:** 2026-05-05
> **关联分析:** Prompt 系统全面扫描（2026-05-05 brainstorming）

---

## 🎯 目标

将当前散落在 Python 文件中的 prompt 常量 + 内联 f-string + 3 套并行风格系统，重构为统一管理、可独立迭代、质量一致的 Prompt 体系。

---

## 📊 现状诊断摘要

| 维度 | 现状 | 问题 |
|------|------|------|
| 存储方式 | 4 个模块级常量 + 1 个内联 f-string | 改 prompt = 改代码 = 重新部署 |
| 风格系统 | 3 套并行（`_FALLBACK_STYLES` / `STYLE_TEMPLATES` / Meooo skill） | `style_templates.py` 700+ 行是死代码 |
| 质量一致性 | intent/plan 较好；thinking/reply 偏弱；code_gen 最弱 | 各节点 LLM 身份认知不统一 |
| 全局身份 | ❌ 无 | 没有定义 "PageForge 是谁" |

---

## Phase 1: 抽离 — Prompt 文件化

**目标:** 把所有 prompt 从 Python 代码中抽离到 `backend/app/prompts/*.md` 文件，实现改 prompt 不改代码。

### Task 1.1: 创建 prompts 目录和加载器

**Files:**
- Create: `backend/app/prompts/__init__.py`
- Create: `backend/app/prompts/loader.py`

**设计:**

```
backend/app/prompts/
├── __init__.py          # 导出 load_prompt() / reload_prompts()
├── loader.py            # 文件扫描 + 缓存 + 热加载
├── 00_identity.md       # PageForge 全局身份
├── 01_intent_router.md  # 意图分类 prompt
├── 02_thinking.md       # 思维链 prompt
├── 03_plan.md           # 计划制定 prompt
```

**`loader.py` 核心逻辑:**

```python
import os
from functools import lru_cache

PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))

@lru_cache(maxsize=1)
def load_prompt(name: str) -> str:
    """按文件名加载 prompt 文本（带缓存）"""
    path = os.path.join(PROMPTS_DIR, f"{name}.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def reload_prompts():
    """清除缓存，强制重新加载（用于热更新）"""
    load_prompt.cache_clear()
```

**验收标准:**
- `load_prompt("01_intent_router")` 返回完整 prompt 文本
- 文件不存在时抛出 `FileNotFoundError` 并给出清晰提示

---

### Task 1.2: 迁移 4 个模块级 prompt 常量

**Files:**
- Create: `backend/app/prompts/01_intent_router.md`
- Create: `backend/app/prompts/02_thinking.md`
- Create: `backend/app/prompts/03_plan.md`
- Create: `backend/app/prompts/05_reply.md`
- Modify: `backend/app/graph/nodes/intent_router.py` — 删除 `INTENT_SYSTEM_PROMPT` 常量，改用 `load_prompt("01_intent_router")`
- Modify: `backend/app/graph/nodes/thinking.py` — 删除 `THINKING_SYSTEM_PROMPT` 常量，改用 `load_prompt("02_thinking")`
- Modify: `backend/app/graph/nodes/plan.py` — 删除 `PLAN_SYSTEM_PROMPT` 常量，改用 `load_prompt("03_plan")`
- Modify: `backend/app/graph/nodes/reply.py` — 删除 `REPLY_SYSTEM_PROMPT` 常量，改用 `load_prompt("05_reply")`

**迁移规则:**
- 文件内容 = 原 prompt 常量内容原样搬移
- 文件名编号对应节点执行顺序
- Python 文件中保留注释标记 `# Loaded from prompts/01_intent_router.md`

---

### Task 1.3: 迁移 code_gen 内联 prompt

**Files:**
- Create: `backend/app/prompts/04_code_gen_system.md` — SystemMessage 内容
- Create: `backend/app/prompts/04_code_gen_user.md` — HumanMessage 模板（含 `{user_message}` / `{plan_steps}` / `{ui_style_config}` 占位符）
- Modify: `backend/app/graph/nodes/code_gen.py` — 删除内联 f-string，改用 `load_prompt()` + `.format()`

**`04_code_gen_user.md` 模板:**

```markdown
## 用户需求
{user_message}

## 计划步骤
{plan_steps}

## UI 风格配置
{ui_style_config}

## 生成要求
1. 使用 TypeScript + React 函数组件 + Hooks
2. 组件必须完整可运行，包含所有必要的 import
3. 遵循 React 最佳实践（副作用放 useEffect、事件处理用 useCallback）
4. 样式使用 Tailwind CSS 类名，不使用内联 style（除非动态计算）
5. 组件 Props 需定义 TypeScript interface
6. 输出格式：只返回 TSX 代码，不要包含 markdown 代码块标记或其他说明
```

**验收标准:**
- `code_gen.py` 中不再有任何硬编码的 prompt 字符串
- 使用 `load_prompt("04_code_gen_user").format(...)` 构建最终 prompt

---

### Task 1.4: 新增全局身份 Prompt

**Files:**
- Create: `backend/app/prompts/00_identity.md`

**内容要求:**
- 定义 PageForge 的身份：AI 全栈开发助手
- 能力边界：前端生成（React/TS/Tailwind）、代码解释、调试、文件操作
- 行为准则：中文优先、代码质量优先、安全约束
- 语气风格：专业但不生硬，简洁有力

**使用方式:**
- 各节点 SystemMessage 拼接时，将 00_identity 作为前缀注入
- 或在 `llm_utils.py` 的 `stream_llm()` 中统一 prepend

---

## Phase 2: 统一 — 消灭三套风格系统

**目标:** 选定一套主风格系统，清理冗余，让 style_picker 有清晰的单一数据源。

### Task 2.1: 决策 — 选哪套风格系统？

**选项分析:**

| 方案 | 优势 | 劣势 | 推荐度 |
|------|------|------|--------|
| A. 主推 Meooo skill | 最全，有 Design Tokens + Anti-patterns | 依赖外部 skill 目录结构，格式不透明 | ⭐⭐⭐ |
| B. 主推 style_templates.py | 自带完整 TSX 代码模板 | 700+ 行无人使用，设计可能过时 | ⭐⭐ |
| **C. 新建统一风格系统** | 可控，格式统一，可迭代 | 需要设计新格式 | ⭐⭐⭐⭐⭐ |

**推荐方案 C:** 新建 `backend/app/prompts/06_style_system.md` 作为统一风格定义，合并 Meooo skill 的 Design Tokens 精华 + `_FALLBACK_STYLES` 的简洁格式。

### Task 2.2: 清理 style_templates.py

**Files:**
- Modify: `backend/app/templates/style_templates.py`

**操作:**
- 如果选方案 C：将 `STYLE_TEMPLATES` 标记为 `@deprecated`，添加注释说明已迁移到 prompts/06_style_system.md
- 如果选方案 B：接入 style_picker 使用

### Task 2.3: 统一 style_picker 数据源

**Files:**
- Modify: `backend/app/graph/nodes/style_picker.py`

**操作:**
- 将 `_FALLBACK_STYLES` 从 `intent_router.py` 迁移到 `prompts/06_style_system.md`
- `style_picker` 加载风格时，优先从统一风格系统读取，降级才用 Meooo skill

---

## Phase 3: 增强 — Prompt 质量提升

**目标:** 提升 thinking 和 reply 节点的 prompt 质量，让 LLM 输出更稳定。

### Task 3.1: 增强 THINKING_SYSTEM_PROMPT

**改进点:**
- 增加 "思考深度" 约束：每部分至少 3-5 句话，不能只写标题
- 增加 "技术选型理由"：为什么选这个方案而不是其他
- 增加 "风险预判"：可能遇到的问题和应对策略
- 增加输出格式示例

### Task 3.2: 增强 REPLY_SYSTEM_PROMPT

**改进点:**
- 定义 PageForge 的人格特征（专业、简洁、友好）
- 区分不同 intent 的回复策略：
  - `code_gen` 完成：列出文件清单 + 运行提示
  - `code_edit` 完成：说明改了什么 + 变更摘要
  - `explain` 概念：用比喻 + 代码示例
  - `chat` 闲聊：轻松自然，适当幽默
- 增加 "禁止事项"：不要过度承诺、不要生成未经验证的信息

### Task 3.3: 增强 code_gen SystemMessage

**改进点:**
- 从一句话扩展为完整的角色定义
- 增加技术栈约束（React 19 / TypeScript strict / Tailwind / Vite）
- 增加代码规范（命名约定、文件结构、注释要求）
- 增加安全约束（不使用 eval / document.write / innerHTML）

---

## 📁 最终目录结构

```
backend/app/prompts/
├── __init__.py
├── loader.py
├── 00_identity.md          # PageForge 全局身份
├── 01_intent_router.md     # 意图分类
├── 02_thinking.md          # 思维链（增强版）
├── 03_plan.md              # 计划制定
├── 04_code_gen_system.md   # 代码生成 SystemMessage（增强版）
├── 04_code_gen_user.md     # 代码生成 HumanMessage 模板
├── 05_reply.md             # 回复生成（增强版）
└── 06_style_system.md      # 统一风格系统（新增）
```

---

## ⏱️ 排期建议

| Phase | 任务 | 预计时间 | 依赖 |
|-------|------|----------|------|
| Phase 1 | 抽离 prompt 到文件 | 1 天 | 无 |
| Phase 1 | 新增全局身份 | 0.5 天 | Task 1.1 |
| Phase 2 | 统一风格系统 | 1-2 天 | Phase 1 完成 |
| Phase 3 | 增强 prompt 质量 | 1 天 | Phase 1 完成 |

**总计:** 3-4 天

---

## ✅ 验收标准

- [ ] 所有 prompt 从 Python 文件中移除，存储在 `prompts/*.md`
- [ ] 改 prompt 内容不需要重新部署 Python 服务
- [ ] `style_templates.py` 死代码已清理或标注废弃
- [ ] 全局身份 prompt 被所有节点使用
- [ ] code_gen 的 SystemMessage 和 HumanMessage 都有完整定义
- [ ] 所有现有测试通过
