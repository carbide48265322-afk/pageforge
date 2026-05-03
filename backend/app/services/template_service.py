import json
from typing import Dict, List, Any
from pathlib import Path
from fastapi import HTTPException
from app.templates.style_templates import (
    StyleTemplate, TemplateCategory,
    get_template, get_templates_by_category, get_all_templates, get_template_categories
)
from app.services.session_service import SessionService
from app.services.version_service import VersionService
from app.config import DATA_DIR

class TemplateService:
    """风格模板服务"""

    def __init__(self):
        self.session_service = SessionService()
        self.version_service = VersionService()

    def get_template_list(self, category: str = None) -> Dict[str, Any]:
        """获取模板列表"""
        if category:
            try:
                template_category = TemplateCategory(category)
                templates = get_templates_by_category(template_category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的模板类别: {category}")
        else:
            templates = get_all_templates()

        return {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "category": t.category.value,
                    "description": t.description,
                    "preview_image": t.preview_image,
                    "color_scheme": {
                        "primary": t.color_scheme.primary,
                        "secondary": t.color_scheme.secondary,
                        "accent": t.color_scheme.accent
                    }
                }
                for t in templates
            ]
        }

    def get_template_detail(self, template_id: str) -> Dict[str, Any]:
        """获取模板详情"""
        template = get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")

        return {
            "id": template.id,
            "name": template.name,
            "category": template.category.value,
            "description": template.description,
            "preview_image": template.preview_image,
            "color_scheme": {
                "primary": template.color_scheme.primary,
                "secondary": template.color_scheme.secondary,
                "accent": template.color_scheme.accent,
                "background": template.color_scheme.background,
                "surface": template.color_scheme.surface,
                "text_primary": template.color_scheme.text_primary,
                "text_secondary": template.color_scheme.text_secondary,
                "success": template.color_scheme.success,
                "warning": template.color_scheme.warning,
                "error": template.color_scheme.error
            },
            "typography": {
                "font_family": template.typography.font_family,
                "heading_font": template.typography.heading_font,
                "body_font": template.typography.body_font,
                "code_font": template.typography.code_font,
                "base_size": template.typography.base_size,
                "scale_ratio": template.typography.scale_ratio
            },
            "spacing": {
                "base_unit": template.spacing.base_unit,
                "scale_ratio": template.spacing.scale_ratio
            },
            "components": {
                "button_radius": template.components.button_radius,
                "card_radius": template.components.card_radius,
                "input_radius": template.components.input_radius,
                "shadow_level": template.components.shadow_level,
                "border_width": template.components.border_width
            },
            "tailwind_config": template.tailwind_config,
            "css_variables": template.css_variables
        }

    def apply_template(self, session_id: str, template_id: str) -> Dict[str, Any]:
        """应用模板到会话"""
        template = get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")

        session = self.session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

        # 生成React项目文件
        project_files = self._generate_react_project_from_template(template)

        # 保存项目文件到会话
        version = self.version_service.save_version(
            session_id=session_id,
            html=project_files["main_component"],  # 主组件作为预览
            summary=f"应用React风格模板: {template.name}",
            trigger_message=f"应用{template.category.value}风格模板",
            parent_version=session.current_base_version if session.current_base_version > 0 else None,
            metadata={
                "template_id": template.id,
                "template_name": template.name,
                "project_files": project_files,
                "tailwind_config": template.tailwind_config,
                "css_variables": template.css_variables
            }
        )

        # 更新会话基准版本
        session.current_base_version = version.version
        self.session_service.save_session(session)

        return {
            "success": True,
            "template_id": template_id,
            "template_name": template.name,
            "version": version.version,
            "css_variables": template.css_variables,
            "tailwind_config": template.tailwind_config,
            "project_files": project_files,
            "message": f"AI已根据您的需求自动选择了{template.name}风格模板并生成React项目"
        }

    def get_categories(self) -> Dict[str, Any]:
        """获取所有模板类别"""
        categories = get_template_categories()
        return {
            "categories": [
                {
                    "name": category_name,
                    "display_name": self._get_category_display_name(category_name),
                    "templates": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "description": t.description,
                            "preview_image": t.preview_image
                        }
                        for t in templates
                    ]
                }
                for category_name, templates in categories.items()
            ]
        }

    def _generate_css_from_template(self, template: StyleTemplate) -> str:
        """从模板生成CSS内容"""
        css_vars = []
        for key, value in template.css_variables.items():
            css_vars.append(f"  {key}: {value};")

        css_content = f"""
/* {template.name} 风格模板 */
:root {{
{chr(10).join(css_vars)}
}}

/* 组件样式 */
.btn {{
  border-radius: {template.components.button_radius};
  font-family: {template.typography.body_font};
}}

.card {{
  border-radius: {template.components.card_radius};
  box-shadow: var(--shadow-{template.components.shadow_level});
  border: {template.components.border_width} solid var(--color-border);
}}

.input {{
  border-radius: {template.components.input_radius};
  border: {template.components.border_width} solid var(--color-border);
  font-family: {template.typography.body_font};
}}

/* 排版样式 */
body {{
  font-family: {template.typography.body_font};
  font-size: {template.typography.base_size};
  color: var(--color-text-primary);
  background-color: var(--color-background);
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: {template.typography.heading_font};
  color: var(--color-text-primary);
}}

code {{
  font-family: {template.typography.code_font};
}}
"""
        return css_content

    def _generate_tailwind_config(self, template: StyleTemplate) -> str:
        """生成Tailwind配置"""
        return json.dumps(template.tailwind_config, indent=2)

    def _generate_html_with_template(self, template: StyleTemplate, css_content: str) -> str:
        """生成包含模板样式的HTML"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template.name} - 风格模板</title>
    <style>
{css_content}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>{template.name}</h1>
            <p>{template.description}</p>
        </header>

        <main class="main-content">
            <section class="card">
                <h2>卡片组件示例</h2>
                <p>这是一个使用{template.name}风格的卡片组件。</p>
                <button class="btn">主要按钮</button>
                <button class="btn btn-secondary">次要按钮</button>
            </section>

            <section class="form-section">
                <h2>表单组件示例</h2>
                <input class="input" type="text" placeholder="输入框示例">
                <button class="btn">提交</button>
            </section>
        </main>
    </div>
</body>
</html>
"""
        return html_content

    def _generate_react_project_from_template(self, template: StyleTemplate) -> Dict[str, str]:
        """从模板生成React项目文件"""
        files = {}

        # 生成CSS变量文件
        css_variables_content = self._generate_css_variables(template)
        files["src/styles/variables.css"] = css_variables_content

        # 生成Tailwind配置文件
        tailwind_config_content = self._generate_tailwind_config_content(template)
        files["tailwind.config.js"] = tailwind_config_content

        # 生成全局样式
        global_css_content = self._generate_global_css(template)
        files["src/styles/globals.css"] = global_css_content

        # 生成React组件
        for component in template.react_components:
            files[f"src/{component.file_path}"] = component.content

        # 生成主页面
        main_page_content = self._generate_main_page(template)
        files["src/pages/index.tsx"] = main_page_content

        # 生成App组件
        app_content = self._generate_app_component(template)
        files["src/App.tsx"] = app_content

        # 生成类型定义
        types_content = self._generate_types(template)
        files["src/types/index.ts"] = types_content

        # 生成package.json
        package_json_content = self._generate_package_json(template)
        files["package.json"] = package_json_content

        # 生成README
        readme_content = self._generate_readme(template)
        files["README.md"] = readme_content

        return {
            "files": files,
            "main_component": main_page_content,
            "file_count": len(files)
        }

    def _generate_css_variables(self, template: StyleTemplate) -> str:
        """生成CSS变量文件"""
        css_vars = []
        for key, value in template.css_variables.items():
            css_vars.append(f"  {key}: {value};")

        return f"""
/* {template.name} - CSS变量 */
:root {{
{chr(10).join(css_vars)}
}}

/* Tailwind类映射 */
.bg-primary {{
  background-color: var(--color-primary) !important;
}}

.text-primary {{
  color: var(--color-primary) !important;
}}

.bg-secondary {{
  background-color: var(--color-secondary) !important;
}}

.text-secondary {{
  color: var(--color-text-secondary) !important;
}}

.bg-accent {{
  background-color: var(--color-accent) !important;
}}

.rounded-card {{
  border-radius: {template.components.card_radius};
}}

.rounded-button {{
  border-radius: {template.components.button_radius};
}}

.rounded-input {{
  border-radius: {template.components.input_radius};
}}
"""

    def _generate_tailwind_config_content(self, template: StyleTemplate) -> str:
        """生成Tailwind配置文件"""
        return f"""
/** @type {import('tailwindcss').Config} */
export default {{
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./src/*.{js,jsx,ts,tsx}"
  ],
  theme: {{
    extend: {}
  }},
  plugins: [],
}}
"""

    def _generate_global_css(self, template: StyleTemplate) -> str:
        """生成全局CSS"""
        return f"""
@import './variables.css';
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {{
  body {{
    font-family: {template.typography.body_font};
    font-size: {template.typography.base_size};
    color: var(--color-text-primary);
    background-color: var(--color-background);
  }}

  h1, h2, h3, h4, h5, h6 {{
    font-family: {template.typography.heading_font};
    color: var(--color-text-primary);
  }}

  code {{
    font-family: {template.typography.code_font};
  }}
}}

@layer components {{
  .btn {{
    @apply px-4 py-2 rounded-button font-medium transition-colors;
  }}

  .btn-primary {{
    @apply bg-primary text-white hover:bg-primary/90;
  }}

  .btn-secondary {{
    @apply bg-secondary text-white hover:bg-secondary/90;
  }}

  .card {{
    @apply bg-white rounded-card shadow-md border border-gray-200;
  }}

  .input {{
    @apply w-full px-3 py-2 border border-gray-300 rounded-input focus:ring-2 focus:ring-primary focus:border-transparent;
  }}
}}
"""

    def _generate_main_page(self, template: StyleTemplate) -> str:
        """生成主页面"""
        if template.category == TemplateCategory.ECOMMERCE:
            return self._generate_ecommerce_page(template)
        elif template.category == TemplateCategory.DASHBOARD:
            return self._generate_dashboard_page(template)
        elif template.category == TemplateCategory.VISUALIZATION:
            return self._generate_visualization_page(template)
        else:
            return self._generate_default_page(template)

    def _generate_ecommerce_page(self, template: StyleTemplate) -> str:
        """生成电商页面"""
        return f"""
import React, {{ useState }} from 'react';
import {{ Header }} from '../components/Header';
import {{ ProductCard }} from '../components/ProductCard';

const mockProducts = [
  {{
    id: 1,
    title: '时尚运动鞋',
    price: 299,
    image: 'https://via.placeholder.com/300x200?text=运动鞋',
    description: '舒适透气的运动鞋，适合日常穿着'
  }},
  {{
    id: 2,
    title: '无线蓝牙耳机',
    price: 199,
    image: 'https://via.placeholder.com/300x200?text=耳机',
    description: '高品质音效，长续航蓝牙耳机'
  }},
  {{
    id: 3,
    title: '智能手表',
    price: 899,
    image: 'https://via.placeholder.com/300x200?text=手表',
    description: '多功能智能手表，健康监测专家'
  }}
];

export default function Home() {{
  const [cartItems, setCartItems] = useState(0);

  const handleAddToCart = (productId: number) => {{
    setCartItems(prev => prev + 1);
    console.log('Added to cart:', productId);
  }};

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <section className="mb-12">
          <div className="bg-gradient-to-r from-primary to-secondary rounded-lg p-8 text-white">
            <h1 className="text-4xl font-bold mb-4">欢迎来到购物商城</h1>
            <p className="text-xl opacity-90">发现精选商品，享受优质购物体验</p>
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">热门商品</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockProducts.map(product => (
              <ProductCard
                key={product.id}
                title={product.title}
                price={product.price}
                image={product.image}
                onAddToCart={() => handleAddToCart(product.id)}
              />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}}
"""

    def _generate_dashboard_page(self, template: StyleTemplate) -> str:
        """生成后台管理页面"""
        return f"""
import React, {{ useState }} from 'react';
import {{ BarChart, Users, ShoppingCart, TrendingUp }} from 'lucide-react';

const stats = [
  {{ icon: Users, label: '总用户', value: '12,345', change: '+12%' }},
  {{ icon: ShoppingCart, label: '订单数', value: '8,921', change: '+8%' }},
  {{ icon: TrendingUp, label: '销售额', value: '¥234,567', change: '+15%' }},
  {{ icon: BarChart, label: '转化率', value: '3.2%', change: '+0.5%' }}
];

export default function Dashboard() {{
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-semibold text-gray-900">管理后台</h1>
            <div className="flex items-center space-x-4">
              <button className="btn btn-primary">新建</button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div key={index} className="card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <stat.icon className="h-8 w-8 text-primary" />
              </div>
              <div className="mt-4">
                <span className="text-sm text-green-600 font-medium">{stat.change}</span>
                <span className="text-sm text-gray-500 ml-2">较上月</span>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">最近订单</h3>
            <div className="space-y-3">
              {{[1,2,3,4,5].map(i => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100">
                  <div>
                    <p className="font-medium">订单 #{1000 + i}</p>
                    <p className="text-sm text-gray-600">用户{i}@example.com</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">¥{(Math.random() * 1000).toFixed(2)}</p>
                    <p className="text-sm text-green-600">已完成</p>
                  </div>
                </div>
              ))}}
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">系统状态</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>CPU使用率</span>
                <div className="flex items-center">
                  <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                    <div className="bg-primary h-2 rounded-full" style={{"width": "45%"}}></div>
                  </div>
                  <span className="text-sm">45%</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>内存使用率</span>
                <div className="flex items-center">
                  <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                    <div className="bg-primary h-2 rounded-full" style={{"width": "68%"}}></div>
                  </div>
                  <span className="text-sm">68%</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span>磁盘使用率</span>
                <div className="flex items-center">
                  <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                    <div className="bg-primary h-2 rounded-full" style={{"width": "32%"}}></div>
                  </div>
                  <span className="text-sm">32%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}}
"""

    def _generate_visualization_page(self, template: StyleTemplate) -> str:
        """生成数据可视化页面"""
        return f"""
import React from 'react';
import {{ LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar }} from 'recharts';

const lineData = [
  {{ name: '1月', value: 4000 }},
  {{ name: '2月', value: 3000 }},
  {{ name: '3月', value: 5000 }},
  {{ name: '4月', value: 4500 }},
  {{ name: '5月', value: 6000 }},
  {{ name: '6月', value: 5500 }}
];

const barData = [
  {{ name: '产品A', value: 2400 }},
  {{ name: '产品B', value: 1398 }},
  {{ name: '产品C', value: 9800 }},
  {{ name: '产品D', value: 3908 }},
  {{ name: '产品E', value: 4800 }}
];

export default function DataVisualization() {{
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-semibold">数据可视化大屏</h1>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-400">实时更新</div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-2">总访问量</h3>
            <div className="text-3xl font-bold text-primary">1,234,567</div>
            <div className="text-sm text-green-400 mt-1">+12.5% 较昨日</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-2">活跃用户</h3>
            <div className="text-3xl font-bold text-secondary">45,678</div>
            <div className="text-sm text-green-400 mt-1">+8.2% 较昨日</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-2">转化率</h3>
            <div className="text-3xl font-bold text-accent">3.45%</div>
            <div className="text-sm text-red-400 mt-1">-0.3% 较昨日</div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4">趋势分析</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px'
                  }}
                />
                <Line type="monotone" dataKey="value" stroke="#06B6D4" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4">产品销售</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="value" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}}
"""

    def _generate_default_page(self, template: StyleTemplate) -> str:
        """生成默认页面"""
        return f"""
import React from 'react';

export default function Home() {{
  return (
    <div className="min-h-screen bg-background">
      <header className="bg-surface border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-bold text-text-primary">{template.name}</h1>
            <nav className="flex space-x-4">
              <a href="#" className="text-text-secondary hover:text-text-primary transition-colors">首页</a>
              <a href="#" className="text-text-secondary hover:text-text-primary transition-colors">关于</a>
              <a href="#" className="text-text-secondary hover:text-text-primary transition-colors">联系</a>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-text-primary mb-4">
            欢迎来到 {template.name}
          </h1>
          <p className="text-xl text-text-secondary mb-8">
            {template.description}
          </p>
          <div className="flex justify-center space-x-4">
            <button className="btn btn-primary px-8 py-3">开始使用</button>
            <button className="btn btn-secondary px-8 py-3">了解更多</button>
          </div>
        </div>
      </main>
    </div>
  );
}}
"""

    def _generate_app_component(self, template: StyleTemplate) -> str:
        """生成App组件"""
        return f"""
import React from 'react';
import Home from './pages/index';
import './styles/globals.css';

function App() {{
  return (
    <div className="App">
      <Home />
    </div>
  );
}}

export default App;
"""

    def _generate_types(self, template: StyleTemplate) -> str:
        """生成类型定义"""
        return """
// 通用类型定义
export interface BaseEntity {{
  id: number;
  created_at?: string;
  updated_at?: string;
}}

// 电商相关类型
export interface Product extends BaseEntity {{
  title: string;
  price: number;
  image: string;
  description: string;
  category: string;
  stock: number;
}}

export interface CartItem {{
  product: Product;
  quantity: number;
}}

// 后台管理相关类型
export interface User extends BaseEntity {{
  email: string;
  name: string;
  role: 'admin' | 'user';
  avatar?: string;
}}

export interface Order extends BaseEntity {{
  user_id: number;
  total: number;
  status: 'pending' | 'processing' | 'shipped' | 'completed';
  items: CartItem[];
}}

// API响应类型
export interface ApiResponse<T> {{
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}}
"""

    def _generate_package_json(self, template: StyleTemplate) -> str:
        """生成package.json"""
        deps = {{
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "lucide-react": "^0.263.1",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "typescript": "^5.0.0"
        }}

        # 根据模板类别添加特定依赖
        if template.category == TemplateCategory.VISUALIZATION:
            deps["recharts"] = "^2.5.0"

        return f"""
{{
  "name": "{template.id}-project",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "dev": "v

# 全局模板服务实例
template_service = TemplateService()