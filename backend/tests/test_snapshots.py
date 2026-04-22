"""验证各子图在确认后写入对应的阶段快照和 phase_history（静态代码分析）"""
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _read_source(rel_path: str) -> str:
    return (BACKEND_DIR / rel_path).read_text()


class TestRequirementSnapshot:
    def test_confirm_writes_requirement_snapshot(self):
        """用户确认 PRD 后应写入 requirement_snapshot"""
        src = _read_source("app/graph/subgraphs/requirement.py")
        confirm_block = re.search(r'if action == "confirm":(.*?)(?=else:|\Z)', src, re.DOTALL)
        assert confirm_block, "Missing confirm branch"
        block = confirm_block.group(1)
        assert 'requirement_snapshot' in block, "confirm branch should write requirement_snapshot"
        assert '"confirmed"' in block, "snapshot should have confirmed=True"
        assert '"prd"' in block, "snapshot should include prd"
        assert '"confirmed_at"' in block, "snapshot should have confirmed_at"

    def test_confirm_appends_phase_history(self):
        """确认后应追加 phase_history"""
        src = _read_source("app/graph/subgraphs/requirement.py")
        confirm_block = re.search(r'if action == "confirm":(.*?)(?=else:|\Z)', src, re.DOTALL)
        assert confirm_block, "Missing confirm branch"
        block = confirm_block.group(1)
        assert 'phase_history' in block, "confirm branch should append phase_history"
        assert '"from_phase"' in block, "phase_history should have from_phase"
        assert '"to_phase"' in block, "phase_history should have to_phase"


class TestTechSnapshot:
    def test_finalize_writes_tech_snapshot(self):
        """技术方案确定后应写入 tech_snapshot"""
        src = _read_source("app/graph/subgraphs/tech.py")
        finalize = re.search(r'def _finalize_node\(self.*?\n(.*?)(?=\n    def |\Z)', src, re.DOTALL)
        assert finalize, "Missing _finalize_node method"
        block = finalize.group(1)
        assert 'tech_snapshot' in block, "_finalize_node should write tech_snapshot"
        assert 'combined_proposal' in block, "snapshot should have combined_proposal"
        assert '"confirmed_at"' in block, "snapshot should have confirmed_at"

    def test_finalize_appends_phase_history(self):
        """技术方案确定后应追加 phase_history"""
        src = _read_source("app/graph/subgraphs/tech.py")
        finalize = re.search(r'def _finalize_node\(self.*?\n(.*?)(?=\n    def |\Z)', src, re.DOTALL)
        assert finalize, "Missing _finalize_node method"
        block = finalize.group(1)
        assert 'phase_history' in block, "_finalize_node should append phase_history"


class TestFeatureSnapshot:
    def test_validate_writes_feature_snapshot(self):
        """功能选择确认后应写入 feature_snapshot"""
        src = _read_source("app/graph/subgraphs/feature.py")
        validate = re.search(r'def _validate_node\(self.*?\n(.*?)(?=\n    def |\Z)', src, re.DOTALL)
        assert validate, "Missing _validate_node method"
        block = validate.group(1)
        assert 'feature_snapshot' in block, "_validate_node should write feature_snapshot"
        assert '"project_mode"' in block, "snapshot should have project_mode"
        assert '"confirmed_at"' in block, "snapshot should have confirmed_at"

    def test_validate_appends_phase_history(self):
        """功能选择确认后应追加 phase_history"""
        src = _read_source("app/graph/subgraphs/feature.py")
        validate = re.search(r'def _validate_node\(self.*?\n(.*?)(?=\n    def |\Z)', src, re.DOTALL)
        assert validate, "Missing _validate_node method"
        block = validate.group(1)
        assert 'phase_history' in block, "_validate_node should append phase_history"
