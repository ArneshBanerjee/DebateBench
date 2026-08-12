from abc import ABC, abstractmethod


class Orchestrator(ABC):
    @abstractmethod
    def pick_winner(self, topic: str, round_num: int, responses: dict[str, str]) -> str:
        """Given {anonymous_code: response_text}, return the winning code."""
