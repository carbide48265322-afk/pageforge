#!/bin/bash
# 一键启动 Jupyter Notebook 节点模拟
cd "$(dirname "$0")"
echo "🚀 启动 PageForge 节点模拟 Notebook..."
uv run jupyter notebook nodes_simulation.ipynb --no-browser --port=8889 --NotebookApp.token='' --NotebookApp.password='' &
sleep 3
open "http://localhost:8889/nodes/nodes_simulation.ipynb"
