"""TechSubgraph - 技术方案子图

基于 DebateVotingSubgraph 实现：
1. Frontend Expert 生成前端方案
2. Backend Expert 生成后端方案
3. DevOps Expert 生成部署方案
4. Moderator 主持辩论（最多3轮）
5. 多维度投票聚合
6. 用户确认/调整技术选型
"""

from typing import Any, Dict, List
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .debate import DebateVotingSubgraph, ExpertOpinion, DebateRound, VoteResult


class TechSubgraph(DebateVotingSubgraph):
    """技术方案子图
    
    实现多专家辩论投票的技术选型流程。
    """
    
    name = "tech"
    description = "技术方案辩论与投票"
    max_rounds = 3
    
    def get_experts(self, state: AgentState) -> List[Dict[str, Any]]:
        """获取专家列表
        
        Args:
            state: 当前状态
            
        Returns:
            List[Dict]: 专家列表
        """
        return [
            {
                "id": "frontend_expert",
                "name": "前端专家",
                "persona": "资深前端架构师，精通React、Vue、Angular等现代前端框架"
            },
            {
                "id": "backend_expert",
                "name": "后端专家",
                "persona": "资深后端架构师，精通Node.js、Python、Go等多种后端技术栈"
            },
            {
                "id": "devops_expert",
                "name": "DevOps专家",
                "persona": "资深DevOps工程师，精通Docker、K8s、CI/CD流程设计"
            }
        ]
    
    def debate_round(self, state: AgentState, expert: Dict, round_num: int) -> ExpertOpinion:
        """执行一轮辩论
        
        Args:
            state: 当前状态
            expert: 专家信息
            round_num: 当前轮次
            
        Returns:
            ExpertOpinion: 专家意见
        """
        requirements_doc = state.get("requirements_doc", "")
        design_spec = state.get("design_spec", {})
        
        subgraph_state = state.get(self.get_state_key(), {})
        rounds = subgraph_state.get(self._rounds_key, [])
        
        # 构建提示词
        prompt = self._build_debate_prompt(
            expert, round_num, requirements_doc, design_spec, rounds
        )
        
        # 调用LLM生成方案
        response = llm.invoke([
            SystemMessage(content=f"你是一位{expert['persona']}。请基于项目需求提出技术方案。"),
            HumanMessage(content=prompt),
        ])
        
        content = response.content
        
        # 提取置信度（简化实现，实际可用更复杂的解析）
        confidence = 0.8 if "确定" in content or "推荐" in content else 0.6
        
        # 构建方案结构
        proposal = {
            "expert_id": expert["id"],
            "expert_name": expert["name"],
            "round": round_num,
            "proposal_text": content,
            "key_points": self._extract_key_points(content)
        }
        
        return ExpertOpinion(
            expert_id=expert["id"],
            expert_name=expert["name"],
            opinion=content,
            confidence=confidence,
            proposal=proposal,
            timestamp=datetime.now()
        )
    
    def _build_debate_prompt(self, expert: Dict, round_num: int, 
                            requirements: str, design_spec: Dict, 
                            previous_rounds: List[DebateRound]) -> str:
        """构建辩论提示词"""
        
        base_prompt = f"""作为{expert['name']}，请为以下项目提出技术方案：

产品需求：
{requirements}

设计规范：
{design_spec}

"""
        
        if expert["id"] == "frontend_expert":
            base_prompt += """请提供前端技术方案：
1. 推荐框架（React/Vue/Angular等）及理由
2. UI组件库选择
3. 状态管理方案
4. 构建工具
5. 性能优化建议"""
            
        elif expert["id"] == "backend_expert":
            base_prompt += """请提供后端技术方案：
1. 推荐语言和框架及理由
2. 数据库选择
3. API设计思路
4. 部署架构建议
5. 安全考虑"""
            
        elif expert["id"] == "devops_expert":
            base_prompt += """请提供部署运维方案：
1. 推荐部署平台（云厂商/自建）
2. CI/CD流程设计
3. 监控和日志方案
4. 成本估算
5. 扩展性考虑"""
        
        # 添加前序轮次信息（用于后续轮次）
        if round_num > 1 and previous_rounds:
            base_prompt += f"""

这是第{round_num}轮辩论。前序观点：
"""
            last_round = previous_rounds[-1]
            for op in last_round.opinions:
                if op.expert_id != expert["id"]:
                    base_prompt += f"\n{op.expert_name}: {op.opinion[:200]}..."
            
            base_prompt += "\n\n请针对其他专家的观点进行回应和补充。"
        
        return base_prompt
    
    def _extract_key_points(self, content: str) -> List[str]:
        """提取关键点"""
        lines = content.split('\n')
        key_points = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                key_points.append(line)
        return key_points[:5]  # 最多取5个要点
    
    def check_consensus(self, rounds: List[DebateRound]) -> tuple[bool, float]:
        """检查是否达成共识
        
        Args:
            rounds: 辩论轮次列表
            
        Returns:
            tuple: (是否达成共识, 共识度分数)
        """
        if not rounds:
            return False, 0.0
        
        last_round = rounds[-1]
        opinions = last_round.opinions
        
        if len(opinions) < 3:
            return False, 0.0
        
        # 计算平均置信度
        avg_confidence = sum(op.confidence for op in opinions) / len(opinions)
        
        # 技术方案辩论通常难以完全达成共识，降低阈值
        consensus = avg_confidence > 0.75 and len(rounds) >= 2
        
        return consensus, avg_confidence
    
    def vote(self, rounds: List[DebateRound]) -> VoteResult:
        """执行投票
        
        Args:
            rounds: 辩论轮次列表
            
        Returns:
            VoteResult: 投票结果
        """
        # 收集所有专家的最佳方案
        best_proposals = {}
        
        for round_data in rounds:
            for op in round_data.opinions:
                eid = op.expert_id
                if eid not in best_proposals or op.confidence > best_proposals[eid]["confidence"]:
                    best_proposals[eid] = {
                        "proposal": op.proposal,
                        "confidence": op.confidence
                    }
        
        # 构建综合技术方案（整合三位专家的建议）
        combined_proposal = {
            "frontend": best_proposals.get("frontend_expert", {}).get("proposal", {}),
            "backend": best_proposals.get("backend_expert", {}).get("proposal", {}),
            "devops": best_proposals.get("devops_expert", {}).get("proposal", {}),
            "vote_summary": {
                eid: data["confidence"] 
                for eid, data in best_proposals.items()
            }
        }
        
        return VoteResult(
            winner_id="combined",
            winner_proposal=combined_proposal,
            vote_count={eid: 1 for eid in best_proposals.keys()},
            total_votes=len(best_proposals)
        )
    
    def _finalize_node(self, state: AgentState) -> Dict:
        """结束辩论，整理结果并更新主状态
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 状态更新
        """
        subgraph_state = self._get_subgraph_state(state)
        
        # 确保有结果
        if self._result_key not in subgraph_state:
            rounds = subgraph_state.get(self._rounds_key, [])
            if rounds:
                result = self.vote(rounds)
                subgraph_state[self._result_key] = result
        
        result = subgraph_state.get(self._result_key)
        proposal = result.winner_proposal if result else {}
        
        subgraph_state[self._status_key] = "completed"
        
        # 更新主状态，进入下一阶段
        return {
            self.get_state_key(): subgraph_state,
            "tech_spec": proposal,
            "tech_approved": True,
            "current_phase": "feature",
            "phase": "feature",  # [DEPRECATED] 向后兼容
            "phase_status": "running",
        }
