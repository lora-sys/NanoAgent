"""
规则引擎模块 - NanoAgent
提供确定性的规则检查机制
"""

from typing import Dict, Callable
from loguru import logger


class RuleEngine:
    """确定性规则引擎"""

    def __init__(self):
        """初始化规则引擎"""
        self.rules: Dict[str, Callable] = {
            "stage_1_completion": self._check_stage_1_completion,
            "stage_2_5_completion": self._check_stage_2_5_completion,
            "requirement_confirmed": self._check_requirement_confirmed,
            "has_artifacts": self._check_has_artifacts,
            "has_decisions": self._check_has_decisions,
        }
        logger.info(
            "RuleEngine initialized with rules: " + ", ".join(self.rules.keys())
        )

    def check_rule(self, rule_name: str, context: Dict) -> bool:
        """检查特定规则

        Args:
            rule_name: 规则名称
            context: 上下文字典

        Returns:
            规则检查结果（True/False）
        """
        if rule_name not in self.rules:
            logger.warning(f"Unknown rule: {rule_name}")
            return False

        try:
            result = self.rules[rule_name](context)
            logger.info(f"Rule check: {rule_name} = {result}")
            return result
        except Exception as e:
            logger.error(f"Rule check failed: {rule_name}, error: {e}")
            return False

    def check_all_rules(self, context: Dict) -> Dict[str, bool]:
        """检查所有规则

        Args:
            context: 上下文字典

        Returns:
            所有规则的检查结果
        """
        results = {}
        for rule_name, rule_func in self.rules.items():
            try:
                results[rule_name] = rule_func(context)
            except Exception as e:
                logger.error(f"Rule check failed: {rule_name}, error: {e}")
                results[rule_name] = False
        return results

    def determine_stage_completion(self, stage_id: str, context: Dict) -> bool:
        """确定阶段是否完成（确定性判断）

        Args:
            stage_id: 阶段 ID（如 stage_1, stage_2 等）
            context: 上下文字典

        Returns:
            阶段是否完成
        """
        if stage_id == "stage_1":
            # 阶段 1：需求对齐
            # 规则：需求已确认
            return self._check_stage_1_completion(context)
        elif stage_id in ["stage_2", "stage_3", "stage_4", "stage_5"]:
            # 阶段 2-5：接口设计、逻辑实现、测试计划、部署指南
            # 规则：有交付物
            return self._check_stage_2_5_completion(context)
        else:
            logger.warning(f"Unknown stage_id: {stage_id}")
            return False

    def _check_stage_1_completion(self, context: Dict) -> bool:
        """检查阶段 1 是否完成（需求对齐）

        规则：需求已确认 或 已有交付物
        - 如果需求已确认（requirements_confirmed=True），则认为阶段 1 完成
        - 如果需求未确认但有交付物（artifacts > 0），也认为阶段 1 完成
          （适用于跳过需求确认流程的项目）
        """
        requirements_confirmed = context.get("requirements_confirmed", False)
        artifacts = context.get("artifacts", [])

        # 规则：需求已确认 或 已有交付物
        result = requirements_confirmed or len(artifacts) > 0

        logger.info(
            f"Stage 1 completion check: requirements_confirmed={requirements_confirmed}, "
            f"artifacts_count={len(artifacts)}, result={result}"
        )

        return result

    def _check_stage_2_5_completion(self, context: Dict) -> bool:
        """检查阶段 2-5 是否完成（接口设计、逻辑实现、测试计划、部署指南）

        规则：有交付物
        """
        artifacts = context.get("artifacts", [])
        return len(artifacts) > 0

    def _check_requirement_confirmed(self, context: Dict) -> bool:
        """检查需求是否已确认"""
        return context.get("requirements_confirmed", False)

    def _check_has_artifacts(self, context: Dict) -> bool:
        """检查是否有交付物"""
        artifacts = context.get("artifacts", [])
        return len(artifacts) > 0

    def _check_has_decisions(self, context: Dict) -> bool:
        """检查是否有决策记录"""
        decisions = context.get("decisions", [])
        return len(decisions) > 0

    def add_custom_rule(self, rule_name: str, rule_func: Callable):
        """添加自定义规则

        Args:
            rule_name: 规则名称
            rule_func: 规则函数（接受 context: Dict，返回 bool）
        """
        self.rules[rule_name] = rule_func
        logger.info(f"Added custom rule: {rule_name}")

    def remove_rule(self, rule_name: str):
        """移除规则

        Args:
            rule_name: 规则名称
        """
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed rule: {rule_name}")

    def __repr__(self) -> str:
        return f"RuleEngine(rules={len(self.rules)})"


# 导出
__all__ = ["RuleEngine"]
