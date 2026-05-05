import json
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from app.models.template import StyleTemplate, TemplateCategory
from app.services.session_service import SessionService
from app.config import TEMPLATES_DIR

template_service = None

class TemplateService:
    def __init__(self):
        self.session_service = SessionService()
        # 确保模板目录存在
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    def get_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取模板列表"""
        # 返回简单模板列表
        templates = [
            {
                "id": "modern",
                "name": "现代风格",
                "category": "react",
                "description": "现代简约的设计风格"
            },
            {
                "id": "classic",
                "name": "经典风格",
                "category": "html",
                "description": "传统优雅的设计风格"
            }
        ]

        if category:
            templates = [t for t in templates if t["category"] == category]

        return templates

    def get_template_by_id(self, template_id: str) -> Optional[StyleTemplate]:
        """根据ID获取模板"""
        # 返回模拟模板
        if template_id == "modern":
            return StyleTemplate(
                id="modern",
                name="现代风格",
                description="现代简约的设计风格",
                category=TemplateCategory.REACT,
                css_variables={},
                tailwind_config={},
                typography={},
                components={}
            )
        return None

    def apply_template(self, session_id: str, template_id: str) -> Dict[str, Any]:
        """应用模板到会话"""
        template = self.get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")

        session = self.session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

        # 简单返回成功消息
        return {
            "success": True,
            "message": f"已应用模板: {template.name}"
        }

    def preview_template(self, template_id: str) -> str:
        """预览模板HTML"""
        return "<html><body><h1>模板预览</h1></body></html>"

# 全局实例
template_service = TemplateService()