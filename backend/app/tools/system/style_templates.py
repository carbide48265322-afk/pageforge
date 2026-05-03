from typing import Dict, List, Any
from langchain_core.tools import tool
from app.services.template_service import template_service
from app.core import registry

@registry.register_tool
@tool
def get_available_style_templates(category: str = None) -> Dict[str, Any]:
    """
    获取可用的风格模板列表

    Args:
        category: 模板类别筛选 (ecommerce, dashboard, visualization, portfolio, blog, landing, social, education)

    Returns:
        模板列表和详细信息
    """
    try:
        templates = template_service.get_template_list(category)

        # 格式化返回结果，便于LLM理解
        formatted_templates = []
        for template in templates["templates"]:
            formatted_templates.append({
                "id": template["id"],
                "name": template["name"],
                "category": template["category"],
                "description": template["description"],
                "primary_color": template["color_scheme"]["primary"],
                "secondary_color": template["color_scheme"]["secondary"],
                "accent_color": template["color_scheme"]["accent"]
            })

        return {
            "success": True,
            "category": category or "all",
            "total_templates": len(formatted_templates),
            "templates": formatted_templates
        }

    except Exception as e:
        return {"success": False, "error": f"获取模板列表失败: {str(e)}"}

@registry.register_tool
@tool
def get_template_details(template_id: str) -> Dict[str, Any]:
    """
    获取指定模板的详细信息

    Args:
        template_id: 模板ID

    Returns:
        模板的详细信息，包括颜色方案、字体、组件样式等
    """
    try:
        template = template_service.get_template_detail(template_id)

        # 简化返回信息，便于LLM使用
        return {
            "success": True,
            "template_id": template["id"],
            "name": template["name"],
            "category": template["category"],
            "description": template["description"],
            "color_scheme": {
                "primary": template["color_scheme"]["primary"],
                "secondary": template["color_scheme"]["secondary"],
                "accent": template["color_scheme"]["accent"],
                "background": template["color_scheme"]["background"],
                "surface": template["color_scheme"]["surface"]
            },
            "typography": template["typography"],
            "components": template["components"],
            "usage_guide": f"这是一个{template['category']}风格的模板，适用于{template['description']}。主色调为{template['color_scheme']['primary']}，适合创建具有现代感和专业性的界面。"
        }

    except Exception as e:
        return {"success": False, "error": f"获取模板详情失败: {str(e)}"}

@registry.register_tool
@tool
def apply_style_template(session_id: str, template_id: str) -> Dict[str, Any]:
    """
    将指定的风格模板应用到当前会话

    Args:
        session_id: 会话ID
        template_id: 要应用的模板ID

    Returns:
        应用结果和生成的新版本信息
    """
    try:
        result = template_service.apply_template(session_id, template_id)

        return {
            "success": True,
            "message": f"成功应用模板 {result['template_name']}",
            "template_id": result["template_id"],
            "template_name": result["template_name"],
            "new_version": result["version"],
            "css_variables": result["css_variables"],
            "next_steps": "模板已应用，可以基于此样式继续开发或修改内容。"
        }

    except Exception as e:
        return {"success": False, "error": f"应用模板失败: {str(e)}"}

@registry.register_tool
@tool
def auto_apply_style_template(session_id: str, user_requirement: str) -> Dict[str, Any]:
    """
    根据用户需求自动选择并应用最合适的风格模板
    AI根据用户描述的内容智能决策，无需用户手动选择

    Args:
        session_id: 会话ID
        user_requirement: 用户的需求描述

    Returns:
        自动选择和应用的结果
    """
    try:
        # 关键词匹配规则
        ecommerce_keywords = ["电商", "购物", "商品", "购买", "店铺", "商城", "零售", "交易", "shop", "store"]
        dashboard_keywords = ["后台", "管理", "系统", "admin", "dashboard", "控制台", "管理界面", "管理系统"]
        visualization_keywords = ["数据", "图表", "统计", "分析", "大屏", "可视化", "dashboard", "图表", "统计", "报表"]
        portfolio_keywords = ["作品", "展示", "个人", "简历", "portfolio", "作品展示", "个人网站"]
        blog_keywords = ["博客", "文章", "写作", "blog", "博客网站", "文章发布"]
        landing_keywords = ["营销", "推广", "宣传", "landing", "活动", "促销", "产品页"]
        social_keywords = ["社交", "社区", "聊天", "论坛", "social", "朋友圈", "微博"]
        education_keywords = ["教育", "学习", "课程", "教学", "培训", "education", "在线学习"]

        # 转换为小写便于匹配
        requirement_lower = user_requirement.lower()

        selected_template_id = None
        reason = ""

        # 电商类
        if any(keyword in requirement_lower for keyword in ecommerce_keywords):
            if any(keyword in requirement_lower for keyword in ["母婴", "家居", "温暖", "温馨"]):
                selected_template_id = "ecommerce_warm"
                reason = "检测到电商需求，且包含母婴/家居相关内容，选择温暖电商风格"
            else:
                selected_template_id = "ecommerce_modern"
                reason = "检测到电商需求，选择现代电商风格"

        # 后台管理类
        elif any(keyword in requirement_lower for keyword in dashboard_keywords):
            selected_template_id = "dashboard_corporate"
            reason = "检测到后台管理需求，选择企业后台风格"

        # 数据可视化类
        elif any(keyword in requirement_lower for keyword in visualization_keywords):
            selected_template_id = "visualization_dark"
            reason = "检测到数据可视化需求，选择深色可视化风格"

        # 其他类别的自动匹配...
        elif any(keyword in requirement_lower for keyword in portfolio_keywords):
            selected_template_id = "portfolio_modern"  # 需要添加这个模板
            reason = "检测到作品展示需求，选择现代作品展示风格"

        elif any(keyword in requirement_lower for keyword in blog_keywords):
            selected_template_id = "blog_elegant"  # 需要添加这个模板
            reason = "检测到博客需求，选择优雅博客风格"

        elif any(keyword in requirement_lower for keyword in landing_keywords):
            selected_template_id = "landing_conversion"  # 需要添加这个模板
            reason = "检测到营销落地页需求，选择高转化率营销风格"

        elif any(keyword in requirement_lower for keyword in social_keywords):
            selected_template_id = "social_modern"  # 需要添加这个模板
            reason = "检测到社交应用需求，选择现代社交风格"

        elif any(keyword in requirement_lower for keyword in education_keywords):
            selected_template_id = "education_clean"  # 需要添加这个模板
            reason = "检测到教育学习需求，选择清爽教育风格"

        # 默认选择
        if not selected_template_id:
            selected_template_id = "dashboard_corporate"
            reason = "未检测到特定需求，默认选择企业后台风格"

        # 应用选中的模板
        result = template_service.apply_template(session_id, selected_template_id)

        return {
            "success": True,
            "reasoning": reason,
            "selected_template_id": selected_template_id,
            "template_name": result["template_name"],
            "new_version": result["version"],
            "message": f"AI已根据您的需求自动选择了{result['template_name']}风格模板并应用"
        }

    except Exception as e:
        return {"success": False, "error": f"自动应用模板失败: {str(e)}"}


@registry.register_tool
@tool
def get_template_categories() -> Dict[str, Any]:
    """
    获取所有可用的模板类别

    Returns:
        模板类别列表和每个类别的模板数量
    """
    try:
        categories = template_service.get_categories()

        # 格式化类别信息
        formatted_categories = []
        for category in categories["categories"]:
            formatted_categories.append({
                "name": category["name"],
                "display_name": category["display_name"],
                "template_count": len(category["templates"]),
                "sample_templates": [
                    {"id": t["id"], "name": t["name"]}
                    for t in category["templates"][:3]  # 每个类别显示前3个模板
                ]
            })

        return {
            "success": True,
            "categories": formatted_categories,
            "total_categories": len(formatted_categories),
            "usage_tips": "用户可以根据项目类型选择合适的模板类别，然后从该类别中选择具体的模板风格。"
        }

    except Exception as e:
        return {"success": False, "error": f"获取模板类别失败: {str(e)}"}