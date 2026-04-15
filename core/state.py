"""Agent 状态管理"""

import json
from pathlib import Path
from typing import Any, Dict, List


class AgentState:
    def __init__(self, spec_path: str = ".spec/manifest.json"):
        self.spec_path = Path(spec_path)
        self._cache: Dict = {}
        self.step_count = 0
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def _load(self) -> Dict:
        if self._cache:
            return self._cache
        if self.spec_path.exists():
            try:
                self._cache = json.loads(self.spec_path.read_text(encoding="utf-8"))
            except Exception:
                self._cache = {}
        return self._cache

    def _save(self):
        try:
            self.spec_path.parent.mkdir(parents=True, exist_ok=True)
            self.spec_path.write_text(
                json.dumps(self._cache, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    def update_spec(self, updates: Dict[str, Any]):
        spec = self._load()
        spec.update(updates)
        self._save()

    def add_artifact(self, path: str, description: str = ""):
        spec = self._load()
        entry = {"path": path, "description": description}
        if entry not in spec.setdefault("artifacts", []):
            spec["artifacts"].append(entry)
            self._save()

    def add_decision(self, decision: str, rationale: str = ""):
        spec = self._load()
        entry = {"decision": decision, "rationale": rationale}
        if entry not in spec.setdefault("decisions", []):
            spec["decisions"].append(entry)
            self._save()

    def update_stage(self, stage_id: str, status: str, updates: Dict = None):
        spec = self._load()
        spec["current_stage"] = stage_id
        stages = spec.setdefault("stages", [])
        for s in stages:
            if s.get("id") == stage_id:
                s["status"] = status
                if updates:
                    s.update(updates)
                break
        else:
            new_stage = {"id": stage_id, "status": status}
            if updates:
                new_stage.update(updates)
            stages.append(new_stage)
        self._save()

    def get_artifacts(self) -> List[str]:
        return [a["path"] for a in self._load().get("artifacts", [])]

    def get_decisions(self) -> List[str]:
        return [d["decision"] for d in self._load().get("decisions", [])]

    def get_current_stage(self) -> str:
        return self._load().get("current_stage", "unknown")

    def get_task(self) -> str:
        return self._load().get("task", "")

    def reset(self):
        self._cache = {}
        self.step_count = 0
        self.messages = []
        if self.spec_path.exists():
            try:
                self.spec_path.unlink()
            except Exception:
                pass
