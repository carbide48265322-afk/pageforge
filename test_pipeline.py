#!/usr/bin/env python3
"""PageForge v2 全链路流水线测试"""
import sys, os, time, json, uuid, logging

logging.basicConfig(level=logging.WARNING)

BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, BACKEND)

from app.graph.nodes.event_emitter import set_event_emitter
from app.graph.nodes.intent_router import intent_router
from app.graph.nodes.thinking import thinking_node
from app.graph.nodes.plan import plan_node
from app.graph.nodes.style_picker import style_picker_node
from app.graph.nodes.code_gen import code_gen_node
from app.graph.nodes.reply import reply_node

# ── Mock 事件发射器 ──
event_log = []
def mock_emitter(event_type, data):
    event_log.append({"type": event_type, "data": data})
set_event_emitter(mock_emitter)

# ── 初始 State ──
def make_state(user_message):
    return {
        "user_message": user_message,
        "session_id": str(uuid.uuid4())[:8],
        "base_html": "",
        "task_list": [],
        "current_html": "",
        "validation_errors": [],
        "iteration_count": 0,
        "fix_count": 0,
        "response_message": "",
        "output_html": None,
        "output_version": 0,
        "is_complete": False,
        "project_type": None,
        "files": [],
        "project_id": None,
        "install_status": "",
        "dev_server_url": None,
        "ui_style": None,
        "intent": None,
        "confidence": 0.0,
        "tags": [],
        "mode": None,
        "complexity": None,
        "model_strategy": {},
        "thought_summary": "",
        "plan_steps": [],
        "ui_style_config": "",
        "status": "",
    }

results = {}
state = make_state("帮我做一个 TODO 应用")

print(f"📝 输入: {state['user_message']}")
print("=" * 60)

# ── Node 1: intent_router ──
print("\n🔍 Node 1: intent_router")
t0 = time.time()
try:
    state = intent_router(state)
    r = {"status": "✅", "intent": state.get("intent"), "complexity": state.get("complexity"), "ui_style": state.get("ui_style"), "time": f"{time.time()-t0:.2f}s"}
except Exception as e:
    r = {"status": "❌", "error": str(e)[:100], "time": f"{time.time()-t0:.2f}s"}
results["intent_router"] = r
print(f"  {r}")

# ── Node 2: thinking ──
print("\n🤔 Node 2: thinking")
t0 = time.time()
try:
    state = thinking_node(state)
    t = state.get("thought_summary", "")
    r = {"status": "✅", "length": len(t), "preview": t[:80]+"..." if len(t)>80 else t, "time": f"{time.time()-t0:.2f}s"}
except Exception as e:
    r = {"status": "❌", "error": str(e)[:100], "time": f"{time.time()-t0:.2f}s"}
results["thinking"] = r
print(f"  {r}")

# ── Node 3: plan ──
print("\n📋 Node 3: plan")
t0 = time.time()
try:
    state = plan_node(state)
    steps = state.get("plan_steps", [])
    r = {"status": "✅", "steps": len(steps), "detail": [f"[{s.get('type')}] {s.get('label')}" for s in steps], "time": f"{time.time()-t0:.2f}s"}
except Exception as e:
    r = {"status": "❌", "error": str(e)[:100], "time": f"{time.time()-t0:.2f}s"}
results["plan"] = r
print(f"  {r}")

# ── Node 4: style_picker ──
print("\n🎨 Node 4: style_picker")
t0 = time.time()
try:
    state = style_picker_node(state)
    cfg = state.get("ui_style_config", "")
    r = {"status": "✅", "style": state.get("ui_style"), "config_len": len(cfg), "time": f"{time.time()-t0:.2f}s"}
except Exception as e:
    r = {"status": "❌", "error": str(e)[:100], "time": f"{time.time()-t0:.2f}s"}
results["style_picker"] = r
print(f"  {r}")

# ── Node 5: code_gen ──
print("\n⚙️ Node 5: code_gen")
t0 = time.time()
try:
    state = code_gen_node(state)
    files = state.get("files", [])
    r = {"status": "✅", "files": len(files), "detail": [f"{f.get('path')} ({f.get('language')})" for f in files], "project_id": state.get("project_id"), "install": state.get("install_status"), "time": f"{time.time()-t0:.2f}s"}
except Exception as e:
    r = {"status": "❌", "error": str(e)[:100], "time": f"{time.time()-t0:.2f}s"}
results["code_gen"] = r
print(f"  {r}")

# ── Node 6: reply ──
print("\n💬 Node 6: reply")
t0 = time.time()
try:
    state = reply_node(state)
    rt = state.get("response_message", "")
    r = {"status": "✅", "length": len(rt), "preview": rt[:100]+"..." if len(rt)>100 else rt, "is_complete": state.get("is_complete"), "time": f"{time.time()-t0:.2f}s"}
except Exception as e:
    r = {"status": "❌", "error": str(e)[:100], "time": f"{time.time()-t0:.2f}s"}
results["reply"] = r
print(f"  {r}")

# ── SSE 事件统计 ──
from collections import Counter
event_types = Counter(e['type'] for e in event_log)

print("\n" + "=" * 60)
print("📊 SSE 事件统计")
print("=" * 60)
print(f"共 {len(event_log)} 个事件:")
for etype, count in sorted(event_types.items()):
    print(f"  {etype:<25} x{count}")

# ── 汇总 ──
print("\n" + "=" * 60)
print("📊 节点测试汇总")
print("=" * 60)
for name, r in results.items():
    icon = r.get("status", "?")
    print(f"  {icon} {name}: {r.get('time','?')}")
    if "error" in r:
        print(f"      ❌ {r['error']}")

ok = sum(1 for r in results.values() if r.get("status") == "✅")
print(f"\n  通过: {ok}/{len(results)}")
