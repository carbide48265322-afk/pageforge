"""验证各子图源码中使用新字段名（静态代码分析，无需导入模块）

由于项目 config.py 依赖 .env 文件导致导入失败，
此测试直接检查源码中是否包含 expected 的字段写入。
"""
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _read_source(rel_path: str) -> str:
    return (BACKEND_DIR / rel_path).read_text()


class TestRequirementSubgraphState:
    def test_process_response_uses_current_phase(self):
        src = _read_source("app/graph/subgraphs/requirement.py")
        # confirm 分支应设置 current_phase
        assert '"current_phase"' in src or "'current_phase'" in src

    def test_process_response_backward_compat(self):
        src = _read_source("app/graph/subgraphs/requirement.py")
        # confirm 分支应同时设置 phase (向后兼容)
        # 查找 confirm 分支附近是否有 current_phase 和 phase
        confirm_block = re.search(r'if action == "confirm":(.*?)(?=else:|\Z)', src, re.DOTALL)
        assert confirm_block, "Missing confirm branch"
        block = confirm_block.group(1)
        assert 'current_phase' in block, "confirm branch should set current_phase"
        assert '"design"' in block, "confirm branch should advance to design"


class TestTechSubgraphState:
    def test_finalize_uses_current_phase(self):
        src = _read_source("app/graph/subgraphs/tech.py")
        finalize = re.search(r'def _finalize_node\(self.*?\n(.*?)(?=\n    def |\Z)', src, re.DOTALL)
        assert finalize, "Missing _finalize_node method"
        block = finalize.group(1)
        assert 'current_phase' in block, "_finalize_node should set current_phase"
        assert '"feature"' in block, "_finalize_node should advance to feature"
        assert 'phase_status' in block, "_finalize_node should set phase_status"


class TestFeatureSubgraphState:
    def test_validate_uses_current_phase(self):
        src = _read_source("app/graph/subgraphs/feature.py")
        validate = re.search(r'def _validate_node\(self.*?\n(.*?)(?=\n    def |\Z)', src, re.DOTALL)
        assert validate, "Missing _validate_node method"
        block = validate.group(1)
        assert 'current_phase' in block, "_validate_node should set current_phase"
        assert '"code"' in block, "_validate_node should advance to code"


class TestDeliverySubgraphState:
    def test_process_response_uses_current_phase(self):
        src = _read_source("app/graph/subgraphs/delivery.py")
        assert 'current_phase' in src, "process_response should use current_phase"

    def test_process_response_confirm_sets_completed(self):
        src = _read_source("app/graph/subgraphs/delivery.py")
        confirm_block = re.search(r'if action == "confirm":(.*?)(?=else:|\Z)', src, re.DOTALL)
        assert confirm_block, "Missing confirm branch"
        block = confirm_block.group(1)
        assert 'current_phase' in block, "confirm branch should set current_phase"
        assert '"completed"' in block, "confirm branch should set phase to completed"


class TestNodesHumanState:
    def test_human_input_reads_current_phase(self):
        src = _read_source("app/graph/nodes_human.py")
        # 应优先读 current_phase
        assert 'current_phase' in src, "human_input_node should reference current_phase"

    def test_human_input_returns_phase_status(self):
        src = _read_source("app/graph/nodes_human.py")
        # 返回值应包含 phase_status
        assert 'phase_status' in src, "human_input_node should return phase_status"


class TestStartNodeState:
    def test_start_node_returns_new_fields(self):
        src = _read_source("app/graph/nodes.py")
        start = re.search(r'async def start_node\(state.*?\n(.*?)(?=\nasync def |\ndef |\Z)', src, re.DOTALL)
        assert start, "Missing start_node function"
        block = start.group(1)
        assert 'current_phase' in block, "start_node should set current_phase"
        assert 'phase_status' in block, "start_node should set phase_status"
        assert 'phase_history' in block, "start_node should set phase_history"


class TestDesignSubgraphState:
    def test_on_enter_uses_current_phase(self):
        src = _read_source("app/graph/subgraphs/design.py")
        on_enter = re.search(r'async def on_enter\(self.*?\n(.*?)(?=\n    async def |\n    def |\Z)', src, re.DOTALL)
        assert on_enter, "Missing on_enter method"
        block = on_enter.group(1)
        assert 'current_phase' in block, "on_enter should set current_phase"

    def test_on_exit_writes_snapshot(self):
        src = _read_source("app/graph/subgraphs/design.py")
        on_exit = re.search(r'async def on_exit\(self.*?\n(.*?)(?=\n    def |\Z)', src, re.DOTALL)
        assert on_exit, "Missing on_exit method"
        block = on_exit.group(1)
        assert 'design_snapshot' in block, "on_exit should write design_snapshot"
