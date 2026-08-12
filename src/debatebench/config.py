from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class AgentConfig(BaseModel):
    name: str
    model: str


class OrchestratorConfig(BaseModel):
    mode: Literal["llm", "human"]
    model: str | None = None


class DebateConfig(BaseModel):
    topic: str
    rounds: int
    agents: list[AgentConfig]
    orchestrator: OrchestratorConfig
    max_tokens: int = 300

    def model_post_init(self, __context) -> None:
        if len(self.agents) < 2:
            raise ValueError("at least 2 agents are required")
        if self.orchestrator.mode == "llm" and not self.orchestrator.model:
            raise ValueError("orchestrator.model is required when mode is 'llm'")


def load_config(path: str | Path) -> DebateConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return DebateConfig(**data)
