from .base import Orchestrator


class HumanOrchestrator(Orchestrator):
    def pick_winner(self, topic: str, round_num: int, responses: dict[str, str]) -> str:
        print(f"\n--- Round {round_num} | Topic: {topic} ---")
        for code, text in responses.items():
            print(f"\n[{code}]\n{text}")

        codes = list(responses)
        while True:
            choice = input(f"\nPick the winning code {codes}: ").strip()
            if choice in responses:
                return choice
            print("Not a valid code, try again.")
