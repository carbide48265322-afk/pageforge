import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage

from app.graph.nodes.llm_utils import stream_llm


def _make_mock_llm(chunks):
    """创建一个模拟流式 LLM，每次 yield 一个 chunk"""
    mock_llm = MagicMock()
    mock_llm.model_name = "test-model"

    def _stream(messages):
        for c in chunks:
            m = MagicMock()
            m.content = c
            yield m

    mock_llm.stream = _stream
    return mock_llm


class TestStreamLlm:
    def test_basic_streaming(self):
        """正常流式调用：所有 emit 回调都被触发"""
        with patch("app.graph.nodes.llm_utils.get_model_for_node", return_value=_make_mock_llm(["Hello", " World"])):
            events = {"start": 0, "deltas": [], "end": None}
            result = stream_llm(
                node_name="reply",
                state={"model_strategy": {"reply": "chat"}},
                messages=[HumanMessage("hi")],
                emit_start=lambda: events.__setitem__("start", events["start"] + 1),
                emit_delta=lambda c: events["deltas"].append(c),
                emit_end=lambda f: events.__setitem__("end", f),
            )
        assert result == "Hello World"
        assert events["start"] == 1
        assert events["deltas"] == ["Hello", " World"]
        assert events["end"] == "Hello World"

    def test_empty_response(self):
        """LLM 返回空：emit_start 和 emit_end 仍触发，emit_delta 不触发"""
        with patch("app.graph.nodes.llm_utils.get_model_for_node", return_value=_make_mock_llm([])):
            events = {"start": 0, "deltas": [], "end": None}
            result = stream_llm(
                node_name="reply",
                state={},
                messages=[HumanMessage("hi")],
                emit_start=lambda: events.__setitem__("start", events["start"] + 1),
                emit_delta=lambda c: events["deltas"].append(c),
                emit_end=lambda f: events.__setitem__("end", f),
            )
        assert result == ""
        assert events["start"] == 1
        assert events["deltas"] == []
        assert events["end"] == ""

    def test_exception_fallback(self):
        """LLM 抛异常：不崩溃，返回错误占位文本"""
        mock_llm = MagicMock()
        mock_llm.model_name = "test-model"
        mock_llm.stream.side_effect = RuntimeError("API Error")

        with patch("app.graph.nodes.llm_utils.get_model_for_node", return_value=mock_llm):
            events = {"start": 0, "deltas": [], "end": None}
            result = stream_llm(
                node_name="reply",
                state={},
                messages=[HumanMessage("hi")],
                emit_start=lambda: events.__setitem__("start", events["start"] + 1),
                emit_delta=lambda c: events["deltas"].append(c),
                emit_end=lambda f: events.__setitem__("end", f),
            )
        assert "[生成失败" in result
        assert events["start"] == 1
        assert events["end"] == result
