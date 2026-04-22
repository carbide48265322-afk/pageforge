# PageForge Agent 约束

## 生成规则

- 始终生成完整的单文件 HTML（含内联 CSS 和 JS）
- 使用语义化 HTML5 标签
- 默认包含 viewport meta 标签
- CSS 使用现代特性（Flexbox/Grid）

## 质量标准

- HTML 必须通过 validate_html 检查（含安全扫描）
- 页面必须在移动端和桌面端均可正常显示
- 文件大小不超过 500KB
- 安全扫描不得包含越权访问（parent.document、window.top 等）
- 安全扫描不得包含危险函数调用（eval、document.write 等）

## 修改规则

- 修改时保留用户已有的自定义内容
- 每次修改生成新版本，不覆盖历史
- 最小化变更原则

## 详细规范

- 完整设计规范：调用 get_design_rules()
- 页面模板：调用 get_template(type)
- Skill 详细说明：读取 skills/\*/SKILL.md

# PageForge Agent 约束

## 生成规则

- 始终生成完整的单文件 HTML（含内联 CSS 和 JS）
- 使用语义化 HTML5 标签
- 默认包含 viewport meta 标签
- CSS 使用现代特性（Flexbox/Grid）

## 质量标准

- HTML 必须通过 validate_html 检查（含安全扫描）
- 页面必须在移动端和桌面端均可正常显示
- 文件大小不超过 500KB
- 安全扫描不得包含越权访问（parent.document、window.top 等）
- 安全扫描不得包含危险函数调用（eval、document.write 等）

## 修改规则

- 修改时保留用户已有的自定义内容
- 每次修改生成新版本，不覆盖历史
- 最小化变更原则

## 详细规范

- 完整设计规范：调用 get_design_rules()
- 页面模板：调用 get_template(type)
- Skill 详细说明：读取 skills/\*/SKILL.md
