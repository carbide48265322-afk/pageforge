#!/usr/bin/env python3

# 修复 template_service.py 中的 f-string 花括号问题
import re

with open('/Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/services/template_service.py', 'r') as f:
    content = f.read()

# 修复 CSS 变量中的 {chr(10).join(css_vars)}
content = re.sub(r'\{chr\(10\)\.join\(css_vars\)\}', '\\n'.join(css_vars), content)

# 保存修复后的文件
with open('/Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/services/template_service.py', 'w') as f:
    f.write(content)

print("修复完成")