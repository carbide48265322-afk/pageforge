import pytest
from app.graph.state import (
    AgentState, RequirementSnapshot, DesignSnapshot,
    TechSnapshot, FeatureSnapshot, CodeSnapshot, PhaseTransition
)


class TestSnapshots:
    def test_requirement_snapshot_fields(self):
        snapshot: RequirementSnapshot = {
            "confirmed": True,
            "user_input": "做一个博客",
            "clarification_qa": [],
            "prd": "# PRD",
            "confirmed_at": "2026-04-22T17:00:00"
        }
        assert snapshot["confirmed"] is True
        assert isinstance(snapshot["prd"], str)

    def test_design_snapshot_fields(self):
        snapshot: DesignSnapshot = {
            "confirmed": True,
            "style_options": [{"id": "modern"}],
            "selected_style": {"id": "modern", "name": "现代简约"},
            "design_spec": {"primary_color": "#333"},
            "confirmed_at": "2026-04-22T17:00:00"
        }
        assert len(snapshot["style_options"]) >= 1

    def test_phase_transition_fields(self):
        transition: PhaseTransition = {
            "from_phase": "requirement",
            "to_phase": "design",
            "trigger": "user_confirmed",
            "timestamp": "2026-04-22T17:00:00"
        }
        assert transition["from_phase"] == "requirement"


class TestAgentStateFields:
    def test_new_fields_exist(self):
        """新架构要求的核心字段都应可访问"""
        from app.graph import state
        expected_fields = [
            "current_phase", "phase_status",
            "requirement_snapshot", "design_snapshot",
            "tech_snapshot", "feature_snapshot", "code_snapshot",
            "phase_history",
            "tech_spec", "tech_approved",
            "project_mode", "selected_features", "available_features", "feature_approved",
            "design_projects", "selected_style_id", "selected_design",
            "delivery_approved", "revision_feedback",
            "human_input_pending", "human_input_checkpoint_id",
        ]
        annotations = state.AgentState.__annotations__
        for field in expected_fields:
            assert field in annotations, f"Missing field: {field}"

    def test_deprecated_fields_still_exist(self):
        """DEPRECATED 旧字段应暂保留，保证向后兼容"""
        from app.graph import state
        deprecated_fields = [
            "base_html", "phase", "stage", "design_concept",
            "selected_style", "available_styles",
            "demo_html", "demo_instructions", "demo_link", "is_demo_ready",
            "task_list", "current_html", "validation_errors",
            "iteration_count", "fix_count",
            "output_html", "output_version",
        ]
        annotations = state.AgentState.__annotations__
        for field in deprecated_fields:
            assert field in annotations, f"Deprecated field removed: {field}"
