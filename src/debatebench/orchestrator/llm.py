import litellm

from .base import Orchestrator

JUDGE_SYSTEM_PROMPT = (
    "You are judging a debate round. You will be shown several anonymized "
    "arguments, each labeled with a code. Pick the single most persuasive "
    "and well-reasoned argument. Reply with only the winning code, nothing else."
)


class LLMOrchestrator(Orchestrator):
    def __init__(self, model: str):
        self.model = model

    def pick_winner(self, topic: str, round_num: int, responses: dict[str, str]) -> str:
        listing = "\n\n".join(f"[{code}]\n{text}" for code, text in responses.items())
        user_prompt = (
            f"Debate topic: {topic}\nRound: {round_num}\n\n{listing}\n\n"
            f"Which code has the most persuasive argument? Reply with only the code."
        )
        result = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=20,
        )
        reply = result.choices[0].message.content.strip()
        for code in responses:
            if code in reply:
                return code
        raise ValueError(f"orchestrator reply did not match any code: {reply!r}")
