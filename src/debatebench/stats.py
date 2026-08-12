from collections import Counter


class StatsTracker:
    """Write-only sink for round wins, keyed by real agent name. Nothing
    else in the pipeline reads from this during the debate; it only gets
    reported once the debate is over."""

    def __init__(self):
        self._wins: Counter[str] = Counter()

    def record_win(self, agent_name: str) -> None:
        self._wins[agent_name] += 1

    def report(self) -> dict[str, int]:
        return dict(self._wins)
