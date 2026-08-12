import random
import string


def assign_codes(agent_names: list[str]) -> dict[str, str]:
    """Return a fresh {agent_name: anonymous_code} mapping. Codes are
    reshuffled every call so no agent keeps the same code across rounds,
    preventing an orchestrator from tracking an agent by its code."""
    codes = set()
    while len(codes) < len(agent_names):
        codes.add("Agent-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)))
    return dict(zip(agent_names, codes))
