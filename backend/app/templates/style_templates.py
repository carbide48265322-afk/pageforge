from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class TemplateCategory(Enum):
    """模板类别"""
    ECOMMERCE = "ecommerce"      # 电商
    DASHBOARD = "dashboard"      # 中后台管理
    VISUALIZATION = "visualization"  # 数据可视化
    PORTFOLIO = "portfolio"      # 作品展示
    BLOG = "blog"               # 博客
    LANDING = "landing"         # 营销落地页
    SOCIAL = "social"           # 社交应用
    EDUCATION = "education"     # 教育学习

@dataclass
class ColorScheme:
    """颜色方案"""
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    success: str
    warning: str
    error: str

@dataclass
class Typography:
    """字体排版"""
    font_family: str
    heading_font: str
    body_font: str
    code_font: str
    base_size: str
    scale_ratio: str

@dataclass
class Spacing:
    """间距系统"""
    base_unit: str
    scale_ratio: str

@dataclass
class ComponentStyles:
    """组件样式"""
    button_radius: str
    card_radius: str
    input_radius: str
    shadow_level: str
    border_width: str

@dataclass
class ComponentTemplate:
    """组件模板"""
    name: str
    file_path: str
    content: str
    props: List[str]

@dataclass
class StyleTemplate:
    """风格模板"""
    id: str
    name: str
    category: TemplateCategory
    description: str
    preview_image: str
    color_scheme: ColorScheme
    typography: Typography
    spacing: Spacing
    components: ComponentStyles
    tailwind_config: Dict[str, Any]
    css_variables: Dict[str, str]
    react_components: List[ComponentTemplate]  # React组件模板
    project_structure: Dict[str, Any]  # 项目文件结构

# 预设模板数据
STYLE_TEMPLATES = {
    # 电商模板
    "ecommerce_modern": StyleTemplate(
        id="ecommerce_modern",
        name="现代电商",
        category=TemplateCategory.ECOMMERCE,
        description="现代简约的电商风格，适合时尚、数码类产品",
        preview_image="/templates/previews/ecommerce_modern.png",
        color_scheme=ColorScheme(
            primary="#3B82F6",
            secondary="#10B981",
            accent="#F59E0B",
            background="#FFFFFF",
            surface="#F8FAFC",
            text_primary="#1F2937",
            text_secondary="#6B7280",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444"
        ),
        typography=Typography(
            font_family="'Inter', sans-serif",
            heading_font="'Poppins', sans-serif",
            body_font="'Inter', sans-serif",
            code_font="'Fira Code', monospace",
            base_size="16px",
            scale_ratio="1.25"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.5"
        ),
        components=ComponentStyles(
            button_radius="8px",
            card_radius="12px",
            input_radius="6px",
            shadow_level="md",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#3B82F6",
                        "secondary": "#10B981",
                        "accent": "#F59E0B"
                    },
                    "borderRadius": {
                        "card": "12px",
                        "button": "8px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#3B82F6",
            "--color-secondary": "#10B981",
            "--color-accent": "#F59E0B",
            "--color-background": "#FFFFFF",
            "--color-surface": "#F8FAFC",
            "--color-text-primary": "#1F2937",
            "--color-text-secondary": "#6B7280"
        },
        react_components=[
            ComponentTemplate(
                name="ProductCard",
                file_path="components/ProductCard.tsx",
                content="""import React from 'react';

interface ProductCardProps {
  title: string;
  price: number;
  image: string;
  onAddToCart: () => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ title, price, image, onAddToCart }) => {
  return (
    <div className=\"bg-white rounded-card shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow\">
      <img src={image} alt={title} className=\"w-full h-48 object-cover\" />
      <div className=\"p-4\">
        <h3 className=\"font-semibold text-text-primary mb-2\">{title}</h3>
        <div className=\"flex items-center justify-between\">
          <span className=\"text-lg font-bold text-primary\">¥{price}</span>
          <button
            onClick={onAddToCart}
            className=\"px-4 py-2 bg-primary text-white rounded-button hover:bg-primary/90 transition-colors\"
          >
            加入购物车
          </button>
        </div>
      </div>
    </div>
  );
};""",
                props=["title", "price", "image", "onAddToCart"]
            ),
            ComponentTemplate(
                name="Header",
                file_path="components/Header.tsx",
                content="""import React from 'react';
import { ShoppingCart, User, Search } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className=\"bg-white border-b border-gray-200 sticky top-0 z-50\">
      <div className=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\">
        <div className=\"flex items-center justify-between h-16\">
          <div className=\"flex items-center\">
            <h1 className=\"text-xl font-bold text-primary\">购物商城</h1>
          </div>

          <div className=\"flex-1 max-w-lg mx-8\">
            <div className=\"relative\">
              <Search className=\"absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400\" size={20} />
              <input
                type=\"text\"
                placeholder=\"搜索商品...\"
                className=\"w-full pl-10 pr-4 py-2 border border-gray-300 rounded-input focus:ring-2 focus:ring-primary focus:border-transparent\"
              />
            </div>
          </div>

          <div className=\"flex items-center space-x-4\">
            <button className=\"p-2 text-gray-600 hover:text-primary transition-colors\">
              <User size={20} />
            </button>
            <button className=\"p-2 text-gray-600 hover:text-primary transition-colors relative\">
              <ShoppingCart size={20} />
              <span className=\"absolute -top-1 -right-1 bg-accent text-white text-xs rounded-full h-5 w-5 flex items-center justify-center\">
                3
              </span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};""",
                props=[]
            )
        ],
        project_structure={
            "src/": {
                "components/": ["ProductCard.tsx", "Header.tsx", "Footer.tsx"],
                "pages/": ["Home.tsx", "ProductList.tsx", "ProductDetail.tsx", "Cart.tsx"],
                "styles/": ["globals.css", "tailwind.css"],
                "types/": ["product.ts", "cart.ts"],
                "utils/": ["api.ts", "format.ts"]
            }
        }
    ),

    "ecommerce_warm": StyleTemplate(
        id="ecommerce_warm",
        name="温暖电商",
        category=TemplateCategory.ECOMMERCE,
        description="温暖亲切的电商风格，适合母婴、家居类产品",
        preview_image="/templates/previews/ecommerce_warm.png",
        color_scheme=ColorScheme(
            primary="#EA580C",
            secondary="#D97706",
            accent="#059669",
            background="#FFFBF5",
            surface="#FEF3C7",
            text_primary="#92400E",
            text_secondary="#A16207",
            success="#059669",
            warning="#D97706",
            error="#DC2626"
        ),
        typography=Typography(
            font_family="'Nunito', sans-serif",
            heading_font="'Merriweather', serif",
            body_font="'Nunito', sans-serif",
            code_font="'Source Code Pro', monospace",
            base_size="16px",
            scale_ratio="1.3"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.6"
        ),
        components=ComponentStyles(
            button_radius="12px",
            card_radius="16px",
            input_radius="8px",
            shadow_level="sm",
            border_width="2px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#EA580C",
                        "secondary": "#D97706",
                        "accent": "#059669"
                    },
                    "borderRadius": {
                        "card": "16px",
                        "button": "12px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#EA580C",
            "--color-secondary": "#D97706",
            "--color-accent": "#059669",
            "--color-background": "#FFFBF5",
            "--color-surface": "#FEF3C7",
            "--color-text-primary": "#92400E",
            "--color-text-secondary": "#A16207"
        }
    ),

    # 中后台管理模板
    "dashboard_corporate": StyleTemplate(
        id="dashboard_corporate",
        name="企业后台",
        category=TemplateCategory.DASHBOARD,
        description="专业严谨的企业级后台管理风格",
        preview_image="/templates/previews/dashboard_corporate.png",
        color_scheme=ColorScheme(
            primary="#1F2937",
            secondary="#374151",
            accent="#3B82F6",
            background="#F9FAFB",
            surface="#FFFFFF",
            text_primary="#111827",
            text_secondary="#6B7280",
            success="#059669",
            warning="#D97706",
            error="#DC2626"
        ),
        typography=Typography(
            font_family="'Roboto', sans-serif",
            heading_font="'Roboto', sans-serif",
            body_font="'Roboto', sans-serif",
            code_font="'Roboto Mono', monospace",
            base_size="14px",
            scale_ratio="1.2"
        ),
        spacing=Spacing(
            base_unit="8px",
            scale_ratio="1.5"
        ),
        components=ComponentStyles(
            button_radius="4px",
            card_radius="6px",
            input_radius="4px",
            shadow_level="sm",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#1F2937",
                        "secondary": "#374151",
                        "accent": "#3B82F6"
                    },
                    "borderRadius": {
                        "card": "6px",
                        "button": "4px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#1F2937",
            "--color-secondary": "#374151",
            "--color-accent": "#3B82F6",
            "--color-background": "#F9FAFB",
            "--color-surface": "#FFFFFF",
            "--color-text-primary": "#111827",
            "--color-text-secondary": "#6B7280"
        }
    ),

    # 数据可视化模板
    "visualization_dark": StyleTemplate(
        id="visualization_dark",
        name="深色可视化",
        category=TemplateCategory.VISUALIZATION,
        description="专业的数据可视化深色主题",
        preview_image="/templates/previews/visualization_dark.png",
        color_scheme=ColorScheme(
            primary="#06B6D4",
            secondary="#8B5CF6",
            accent="#F59E0B",
            background="#0F172A",
            surface="#1E293B",
            text_primary="#F1F5F9",
            text_secondary="#94A3B8",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444"
        ),
        typography=Typography(
            font_family="'JetBrains Mono', monospace",
            heading_font="'Inter', sans-serif",
            body_font="'Inter', sans-serif",
            code_font="'JetBrains Mono', monospace",
            base_size="14px",
            scale_ratio="1.25"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.4"
        ),
        components=ComponentStyles(
            button_radius="6px",
            card_radius="8px",
            input_radius="4px",
            shadow_level="lg",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#06B6D4",
                        "secondary": "#8B5CF6",
                        "accent": "#F59E0B"
                    },
                    "borderRadius": {
                        "card": "8px",
                        "button": "6px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#06B6D4",
            "--color-secondary": "#8B5CF6",
            "--color-accent": "#F59E0B",
            "--color-background": "#0F172A",
            "--color-surface": "#1E293B",
            "--color-text-primary": "#F1F5F9",
            "--color-text-secondary": "#94A3B8"
        }
    ),

    # 作品展示模板
    "portfolio_modern": StyleTemplate(
        id="portfolio_modern",
        name="现代作品展示",
        category=TemplateCategory.PORTFOLIO,
        description="现代简约的作品展示风格，适合设计师、开发者展示作品",
        preview_image="/templates/previews/portfolio_modern.png",
        color_scheme=ColorScheme(
            primary="#6366F1",
            secondary="#8B5CF6",
            accent="#EC4899",
            background="#FAFAFA",
            surface="#FFFFFF",
            text_primary="#1F2937",
            text_secondary="#6B7280",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444"
        ),
        typography=Typography(
            font_family="'Inter', sans-serif",
            heading_font="'Playfair Display', serif",
            body_font="'Inter', sans-serif",
            code_font="'Fira Code', monospace",
            base_size="16px",
            scale_ratio="1.3"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.5"
        ),
        components=ComponentStyles(
            button_radius="8px",
            card_radius="12px",
            input_radius="6px",
            shadow_level="md",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#6366F1",
                        "secondary": "#8B5CF6",
                        "accent": "#EC4899"
                    },
                    "borderRadius": {
                        "card": "12px",
                        "button": "8px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#6366F1",
            "--color-secondary": "#8B5CF6",
            "--color-accent": "#EC4899",
            "--color-background": "#FAFAFA",
            "--color-surface": "#FFFFFF",
            "--color-text-primary": "#1F2937",
            "--color-text-secondary": "#6B7280"
        },
        react_components=[],
        project_structure={"src/": {"components/": [], "pages/": []}}
    ),

    # 博客模板
    "blog_elegant": StyleTemplate(
        id="blog_elegant",
        name="优雅博客",
        category=TemplateCategory.BLOG,
        description="优雅简洁的博客风格，适合个人博客、技术文章分享",
        preview_image="/templates/previews/blog_elegant.png",
        color_scheme=ColorScheme(
            primary="#059669",
            secondary="#0D9488",
            accent="#7C3AED",
            background="#FEFEFE",
            surface="#FFFFFF",
            text_primary="#1F2937",
            text_secondary="#4B5563",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444"
        ),
        typography=Typography(
            font_family="'Source Sans Pro', sans-serif",
            heading_font="'Merriweather', serif",
            body_font="'Source Sans Pro', sans-serif",
            code_font="'Source Code Pro', monospace",
            base_size="18px",
            scale_ratio="1.4"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.6"
        ),
        components=ComponentStyles(
            button_radius="6px",
            card_radius="8px",
            input_radius="4px",
            shadow_level="sm",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#059669",
                        "secondary": "#0D9488",
                        "accent": "#7C3AED"
                    },
                    "borderRadius": {
                        "card": "8px",
                        "button": "6px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#059669",
            "--color-secondary": "#0D9488",
            "--color-accent": "#7C3AED",
            "--color-background": "#FEFEFE",
            "--color-surface": "#FFFFFF",
            "--color-text-primary": "#1F2937",
            "--color-text-secondary": "#4B5563"
        },
        react_components=[],
        project_structure={"src/": {"components/": [], "pages/": []}}
    ),

    # 营销落地页模板
    "landing_conversion": StyleTemplate(
        id="landing_conversion",
        name="高转化落地页",
        category=TemplateCategory.LANDING,
        description="专为高转化率设计的营销落地页风格",
        preview_image="/templates/previews/landing_conversion.png",
        color_scheme=ColorScheme(
            primary="#DC2626",
            secondary="#EA580C",
            accent="#F59E0B",
            background="#FFFFFF",
            surface="#F9FAFB",
            text_primary="#111827",
            text_secondary="#6B7280",
            success="#059669",
            warning="#F59E0B",
            error="#EF4444"
        ),
        typography=Typography(
            font_family="'Montserrat', sans-serif",
            heading_font="'Montserrat', sans-serif",
            body_font="'Open Sans', sans-serif",
            code_font="'Roboto Mono', monospace",
            base_size="16px",
            scale_ratio="1.25"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.5"
        ),
        components=ComponentStyles(
            button_radius="8px",
            card_radius="12px",
            input_radius="6px",
            shadow_level="lg",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#DC2626",
                        "secondary": "#EA580C",
                        "accent": "#F59E0B"
                    },
                    "borderRadius": {
                        "card": "12px",
                        "button": "8px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#DC2626",
            "--color-secondary": "#EA580C",
            "--color-accent": "#F59E0B",
            "--color-background": "#FFFFFF",
            "--color-surface": "#F9FAFB",
            "--color-text-primary": "#111827",
            "--color-text-secondary": "#6B7280"
        },
        react_components=[],
        project_structure={"src/": {"components/": [], "pages/": []}}
    ),

    # 社交应用模板
    "social_modern": StyleTemplate(
        id="social_modern",
        name="现代社交",
        category=TemplateCategory.SOCIAL,
        description="现代化的社交应用风格，适合社区、论坛类应用",
        preview_image="/templates/previews/social_modern.png",
        color_scheme=ColorScheme(
            primary="#3B82F6",
            secondary="#10B981",
            accent="#F59E0B",
            background="#F8FAFC",
            surface="#FFFFFF",
            text_primary="#1E293B",
            text_secondary="#64748B",
            success="#10B981",
            warning="#F59E0B",
            error="#EF4444"
        ),
        typography=Typography(
            font_family="'Inter', sans-serif",
            heading_font="'Inter', sans-serif",
            body_font="'Inter', sans-serif",
            code_font="'JetBrains Mono', monospace",
            base_size="16px",
            scale_ratio="1.25"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.5"
        ),
        components=ComponentStyles(
            button_radius="20px",
            card_radius="12px",
            input_radius="20px",
            shadow_level="sm",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#3B82F6",
                        "secondary": "#10B981",
                        "accent": "#F59E0B"
                    },
                    "borderRadius": {
                        "card": "12px",
                        "button": "20px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#3B82F6",
            "--color-secondary": "#10B981",
            "--color-accent": "#F59E0B",
            "--color-background": "#F8FAFC",
            "--color-surface": "#FFFFFF",
            "--color-text-primary": "#1E293B",
            "--color-text-secondary": "#64748B"
        },
        react_components=[],
        project_structure={"src/": {"components/": [], "pages/": []}}
    ),

    # 教育学习模板
    "education_clean": StyleTemplate(
        id="education_clean",
        name="清爽教育",
        category=TemplateCategory.EDUCATION,
        description="清爽简洁的教育学习风格，适合在线课程、学习平台",
        preview_image="/templates/previews/education_clean.png",
        color_scheme=ColorScheme(
            primary="#0D9488",
            secondary="#059669",
            accent="#F59E0B",
            background="#F0FDFA",
            surface="#FFFFFF",
            text_primary="#134E4A",
            text_secondary="#0F766E",
            success="#059669",
            warning="#F59E0B",
            error="#EF4444"
        ),
        typography=Typography(
            font_family="'Open Sans', sans-serif",
            heading_font="'Roboto', sans-serif",
            body_font="'Open Sans', sans-serif",
            code_font="'Source Code Pro', monospace",
            base_size="16px",
            scale_ratio="1.3"
        ),
        spacing=Spacing(
            base_unit="4px",
            scale_ratio="1.5"
        ),
        components=ComponentStyles(
            button_radius="6px",
            card_radius="8px",
            input_radius="6px",
            shadow_level="sm",
            border_width="1px"
        ),
        tailwind_config={
            "theme": {
                "extend": {
                    "colors": {
                        "primary": "#0D9488",
                        "secondary": "#059669",
                        "accent": "#F59E0B"
                    },
                    "borderRadius": {
                        "card": "8px",
                        "button": "6px"
                    }
                }
            }
        },
        css_variables={
            "--color-primary": "#0D9488",
            "--color-secondary": "#059669",
            "--color-accent": "#F59E0B",
            "--color-background": "#F0FDFA",
            "--color-surface": "#FFFFFF",
            "--color-text-primary": "#134E4A",
            "--color-text-secondary": "#0F766E"
        },
        react_components=[],
        project_structure={"src/": {"components/": [], "pages/": []}}
    )
}

def get_template(template_id: str) -> StyleTemplate:
    """获取指定模板"""
    return STYLE_TEMPLATES.get(template_id)

def get_templates_by_category(category: TemplateCategory) -> List[StyleTemplate]:
    """按类别获取模板"""
    return [t for t in STYLE_TEMPLATES.values() if t.category == category]

def get_all_templates() -> List[StyleTemplate]:
    """获取所有模板"""
    return list(STYLE_TEMPLATES.values())

def get_template_categories() -> Dict[str, List[StyleTemplate]]:
    """按类别分组返回模板"""
    categories = {}
    for template in STYLE_TEMPLATES.values():
        category_name = template.category.value
        if category_name not in categories:
            categories[category_name] = []
        categories[category_name].append(template)
    return categories