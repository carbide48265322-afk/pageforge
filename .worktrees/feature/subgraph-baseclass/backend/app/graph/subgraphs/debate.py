"""DebateVotingSubgraph - 辩论投票模式

多专家辩论 + 投票决策流程：
1. 初始化专家列表
2. 每轮辩论：各专家发表意见
3. 汇总观点，检查是否达成共识
4. 未达成 → 下一轮（最多3轮）
5. 达成/超时 → 投票选出最终方案

子类只需实现 debate_round() 方法。
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

from app.graph.state import AgentState
from .base import BaseSubgraph, SubgraphMode


@dataclass
class ExpertOpinion:
    """专家意见"""
    expert_id: str           # 专家标识
    expert_name: str         # 专家名称
    opinion: str             # 观点内容
    confidence: float        # 置信度 0-1
    proposal: Dict[str, Any] # 具体方案
    timestamp: datetime      # 发表时间


@dataclass
class DebateRound:
    """辩论轮次"""
    round_number: int
    opinions: List[ExpertOpinion]
    summary: str             # 本轮观点汇总
    consensus_reached: bool  # 是否达成共识
    consensus_score: float   # 共识度 0-1


@dataclass
class VoteResult:
    """投票结果"""
    winner_id: str           # 获胜方案ID
    winner_proposal: Dict[str, Any]
    vote_count: Dict[str, int]  # 各方案得票数
    total_votes: int


class DebateVotingSubgraph(BaseSubgraph):
    """辩论投票子图基类
    
    实现标准的多专家辩论模板：
    init → round_1 → check_consensus → [round_2...] → vote → finalize
    
    子类必须实现:
        - get_experts(state): 获取专家列表
        - debate_round(state, expert, round_num): 单轮辩论
        
    可选覆盖:
        - check_consensus(rounds): 检查共识
        - vote(rounds): 投票逻辑
    """
    
    mode = SubgraphMode.DEBATE_VOTING
    max_rounds: int = 3      # 最大辩论轮数
    min_consensus: float = 0.7  # 共识阈值
    
    # 状态键
    _experts_key: str = "experts"
    _rounds_key: str = "debate_rounds"
    _current_round_key: str = "current_round"
    _result_key: str = "debate_result"
    _status_key: str = "status"
    
    def _build_internal(self) -> StateGraph:
        """构建辩论投票子图"""
        graph = StateGraph(AgentState)
        
        # 节点
        graph.add_node(f"{self.name}_init", self._init_debate)
        graph.add_node(f"{self.name}_debate", self._debate_round_node)
        graph.add_node(f"{self.name}_check", self._check_consensus_node)
        graph.add_node(f"{self.name}_vote", self._vote_node)
        graph.add_node(f"{self.name}_finalize", self._finalize_node)
        
        # 入口
        graph.set_entry_point(f"{self.name}_init")
        graph.add_edge(f"{self.name}_init", f"{self.name}_debate")
        
        # 辩论 → 检查
        graph.add_edge(f"{self.name}_debate", f"{self.name}_check")
        
        # 检查条件边：继续辩论 / 投票 / 结束
        graph.add_conditional_edges(
            f"{self.name}_check",
            self._next_step,
            {
                "debate": f"{self.name}_debate",    # 继续辩论
                "vote": f"{self.name}_vote",        # 进入投票
                "finalize": f"{self.name}_finalize" # 直接结束
            }
        )
        
        # 投票 → 结束
        graph.add_edge(f"{self.name}_vote", f"{self.name}_finalize")
        graph.add_edge(f"{self.name}_finalize", END)
        
        return graph
    
    def _get_subgraph_state(self, state: AgentState) -> Dict:
        """获取子图私有状态"""
        key = self.get_state_key()
        if key not in state:
            state[key] = {}
        return state[key]
    
    def _init_debate(self, state: AgentState) -> Dict:
        """初始化辩论"""
        subgraph_state = self._get_subgraph_state(state)
        
        experts = self.get_experts(state)
        
        subgraph_state[self._experts_key] = experts
        subgraph_state[self._rounds_key] = []
        subgraph_state[self._current_round_key] = 0
        subgraph_state[self._status_key] = "initialized"
        
        return {self.get_state_key(): subgraph_state}
    
    def _debate_round_node(self, state: AgentState) -> Dict:
        """执行一轮辩论"""
        subgraph_state = self._get_subgraph_state(state)
        
        experts = subgraph_state[self._experts_key]
        current_round = subgraph_state[self._current_round_key] + 1
        
        # 收集各专家意见
        opinions: List[ExpertOpinion] = []
        for expert in experts:
            opinion = self.debate_round(state, expert, current_round)
            opinions.append(opinion)
        
        # 生成本轮汇总
        summary = self._summarize_round(opinions)
        
        # 创建轮次记录
        debate_round = DebateRound(
            round_number=current_round,
            opinions=opinions,
            summary=summary,
            consensus_reached=False,  # 稍后检查
            consensus_score=0.0
        )
        
        # 更新状态
        rounds = subgraph_state[self._rounds_key]
        rounds.append(debate_round)
        subgraph_state[self._rounds_key] = rounds
        subgraph_state[self._current_round_key] = current_round
        subgraph_state[self._status_key] = f"round_{current_round}"
        
        return {self.get_state_key(): subgraph_state}
    
    def _check_consensus_node(self, state: AgentState) -> Dict:
        """检查是否达成共识"""
        subgraph_state = self._get_subgraph_state(state)
        rounds = subgraph_state[self._rounds_key]
        
        if not rounds:
            return {self.get_state_key(): subgraph_state}
        
        current_round = rounds[-1]
        
        # 调用共识检查
        consensus_reached, score = self.check_consensus(rounds)
        
        # 更新当前轮次
        current_round.consensus_reached = consensus_reached
        current_round.consensus_score = score
        
        subgraph_state[self._status_key] = "checking_consensus"
        
        return {self.get_state_key(): subgraph_state}
    
    def _next_step(self, state: AgentState) -> str:
        """决定下一步"""
        subgraph_state = self._get_subgraph_state(state)
        rounds = subgraph_state.get(self._rounds_key, [])
        current_round_num = subgraph_state.get(self._current_round_key, 0)
        
        if not rounds:
            return "debate"
        
        last_round = rounds[-1]
        
        # 达成共识 → 直接结束
        if last_round.consensus_reached:
            return "finalize"
        
        # 超过最大轮数 → 投票
        if current_round_num >= self.max_rounds:
            return "vote"
        
        # 继续辩论
        return "debate"
    
    def _vote_node(self, state: AgentState) -> Dict:
        """执行投票"""
        subgraph_state = self._get_subgraph_state(state)
        rounds = subgraph_state[self._rounds_key]
        
        # 调用投票逻辑
        result = self.vote(rounds)
        
        subgraph_state[self._result_key] = result
        subgraph_state[self._status_key] = "voted"
        
        return {self.get_state_key(): subgraph_state}
    
    def _finalize_node(self, state: AgentState) -> Dict:
        """结束辩论，整理结果"""
        subgraph_state = self._get_subgraph_state(state)
        
        # 确保有结果（可能直接达成共识跳过投票）
        if self._result_key not in subgraph_state:
            rounds = subgraph_state.get(self._rounds_key, [])
            if rounds:
                # 使用最后一轮作为结果
                last_round = rounds[-1]
                # 选择置信度最高的方案
                best_opinion = max(last_round.opinions, key=lambda x: x.confidence)
                result = VoteResult(
                    winner_id=best_opinion.expert_id,
                    winner_proposal=best_opinion.proposal,
                    vote_count={best_opinion.expert_id: 1},
                    total_votes=1
                )
                subgraph_state[self._result_key] = result
        
        subgraph_state[self._status_key] = "completed"
        
        return {self.get_state_key(): subgraph_state}
    
    def _summarize_round(self, opinions: List[ExpertOpinion]) -> str:
        """汇总本轮观点（默认实现）"""
        summaries = []
        for op in opinions:
            summaries.append(f"{op.expert_name}: {op.opinion[:100]}...")
        return "\n".join(summaries)
    
    # ========== 子类必须/可选实现 ==========
    
    @abstractmethod
    def get_experts(self, state: AgentState) -> List[Dict[str, Any]]:
        """获取专家列表（子类必须实现）
        
        Returns:
            List[Dict]: 专家列表，每项包含 id, name, persona 等
            例: [
                {"id": "frontend_expert", "name": "前端专家", "persona": "React专家..."},
                {"id": "backend_expert", "name": "后端专家", "persona": "Go专家..."}
            ]
        """
        pass
    
    @abstractmethod
    def debate_round(self, state: AgentState, expert: Dict, round_num: int) -> ExpertOpinion:
        """单轮辩论（子类必须实现）
        
        Args:
            state: 当前状态
            expert: 专家信息
            round_num: 当前轮次
            
        Returns:
            ExpertOpinion: 专家意见
        """
        pass
    
    def check_consensus(self, rounds: List[DebateRound]) -> tuple[bool, float]:
        """检查是否达成共识（子类可选覆盖）
        
        默认逻辑：
        - 所有专家置信度 > 0.8
        - 方案相似度 > 0.7
        
        Returns:
            tuple: (是否达成共识, 共识度分数)
        """
        if not rounds:
            return False, 0.0
        
        last_round = rounds[-1]
        opinions = last_round.opinions
        
        if len(opinions) < 2:
            return True, 1.0
        
        # 计算平均置信度
        avg_confidence = sum(op.confidence for op in opinions) / len(opinions)
        
        # 简单判断：平均置信度 > 0.8 认为达成共识
        consensus = avg_confidence > self.min_consensus
        
        return consensus, avg_confidence
    
    def vote(self, rounds: List[DebateRound]) -> VoteResult:
        """投票逻辑（子类可选覆盖）
        
        默认逻辑：
        - 汇总所有轮次的方案
        - 选择出现次数最多/置信度最高的方案
        
        Returns:
            VoteResult: 投票结果
        """
        # 收集所有方案
        all_proposals = []
        for round_data in rounds:
            for op in round_data.opinions:
                all_proposals.append({
                    "expert_id": op.expert_id,
                    "proposal": op.proposal,
                    "confidence": op.confidence
                })
        
        # 按专家分组，取每个专家最高置信度的方案
        best_by_expert = {}
        for p in all_proposals:
            eid = p["expert_id"]
            if eid not in best_by_expert or p["confidence"] > best_by_expert[eid]["confidence"]:
                best_by_expert[eid] = p
        
        # 选择置信度最高的
        winner = max(best_by_expert.values(), key=lambda x: x["confidence"])
        
        return VoteResult(
            winner_id=winner["expert_id"],
            winner_proposal=winner["proposal"],
            vote_count={winner["expert_id"]: 1},
            total_votes=len(best_by_expert)
        )
