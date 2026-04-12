"""Deterministic rule checking engine."""

from typing import Dict, Callable, Any, List
from loguru import logger


class RuleEngine:
    def __init__(self):
        self.rules: Dict[str, Callable] = {
            "stage_1_completion": self._check_stage_1_completion,
            "stage_2_5_completion": self._check_stage_2_5_completion,
            "requirement_confirmed": self._check_requirement_confirmed,
            "has_artifacts": self._check_has_artifacts,
            "has_decisions": self._check_has_decisions,
        }
        logger.info(
            f"RuleEngine initialized with rules: {', '.join(self.rules.keys())}"
        )

    def check_rule(self, rule_name: str, context: Dict) -> bool:
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
        results = {}
        for rule_name, rule_func in self.rules.items():
            try:
                results[rule_name] = rule_func(context)
            except Exception as e:
                logger.error(f"Rule check failed: {rule_name}, error: {e}")
                results[rule_name] = False
        return results

    def check_stage_completion(
        self, stage_id: str, artifacts: List[str], decisions: List[Dict[str, Any]]
    ) -> bool:
        context = {
            "artifacts": artifacts,
            "decisions": decisions,
            "requirements_confirmed": len(decisions) > 0,
        }
        return self.determine_stage_completion(stage_id, context)

    def determine_stage_completion(self, stage_id: str, context: Dict) -> bool:
        if stage_id == "stage_1":
            return self._check_stage_1_completion(context)
        elif stage_id in ["stage_2", "stage_3", "stage_4", "stage_5"]:
            return self._check_stage_2_5_completion(context)
        logger.warning(f"Unknown stage_id: {stage_id}")
        return False

    def _check_stage_1_completion(self, context: Dict) -> bool:
        confirmed = context.get("requirements_confirmed", False)
        artifacts = context.get("artifacts", [])
        result = confirmed or len(artifacts) > 0
        logger.info(
            f"Stage 1 completion: confirmed={confirmed}, artifacts={len(artifacts)}, result={result}"
        )
        return result

    def _check_stage_2_5_completion(self, context: Dict) -> bool:
        return len(context.get("artifacts", [])) > 0

    def _check_requirement_confirmed(self, context: Dict) -> bool:
        return context.get("requirements_confirmed", False)

    def _check_has_artifacts(self, context: Dict) -> bool:
        return len(context.get("artifacts", [])) > 0

    def _check_has_decisions(self, context: Dict) -> bool:
        return len(context.get("decisions", [])) > 0
