from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass

class TemplateCategory(str, Enum):
    REACT = "react"
    HTML = "html"
    VUE = "vue"

@dataclass
class StyleTemplate:
    id: str
    name: str
    description: str
    category: TemplateCategory
    css_variables: Dict[str, str]
    tailwind_config: Dict[str, Any]
    typography: Dict[str, str]
    components: Dict[str, Any]

    def __post_init__(self):
        if isinstance(self.category, str):
            self.category = TemplateCategory(self.category)