import litellm

SYSTEM_PROMPT = (
    "You are a debater arguing about the given topic. Give a concise, "
    "persuasive argument in a few sentences. If shown the previous round's "
    "winning argument, respond to it and improve on your own prior answer."
)


class Agent:
    """A debate agent. `model` is a LiteLLM model string, so it may point at
    a hosted API (e.g. "gemini/gemini-1.5-flash") or a local Ollama model
    (e.g. "ollama/llama3.2:1b") interchangeably."""

    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.own_last_response: str | None = None

    def respond(self, topic: str, round_num: int, winning_response: str | None, max_tokens: int) -> str:
        user_prompt = f"Debate topic: {topic}\nRound: {round_num}\n"
        if self.own_last_response:
            user_prompt += f"\nYour previous argument:\n{self.own_last_response}\n"
        if winning_response:
            user_prompt += f"\nThe winning argument from last round:\n{winning_response}\n"
        user_prompt += "\nGive your argument for this round."

        result = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        response = result.choices[0].message.content.strip()
        self.own_last_response = response
        return response
