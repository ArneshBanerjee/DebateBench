from .agent import Agent
from .anonymizer import assign_codes
from .config import DebateConfig
from .orchestrator import HumanOrchestrator, LLMOrchestrator, Orchestrator
from .stats import StatsTracker


def build_orchestrator(config: DebateConfig) -> Orchestrator:
    if config.orchestrator.mode == "llm":
        return LLMOrchestrator(model=config.orchestrator.model)
    return HumanOrchestrator()


def run_debate(config: DebateConfig) -> dict[str, int]:
    agents = [Agent(name=a.name, model=a.model) for a in config.agents]
    orchestrator = build_orchestrator(config)
    stats = StatsTracker()

    winning_response: str | None = None
    for round_num in range(1, config.rounds + 1):
        responses_by_name = {
            agent.name: agent.respond(config.topic, round_num, winning_response, config.max_tokens)
            for agent in agents
        }

        code_by_name = assign_codes(list(responses_by_name))
        anon_responses = {code: responses_by_name[name] for name, code in code_by_name.items()}

        winning_code = orchestrator.pick_winner(config.topic, round_num, anon_responses)
        winning_name = next(name for name, code in code_by_name.items() if code == winning_code)

        stats.record_win(winning_name)
        winning_response = anon_responses[winning_code]

        print(f"Round {round_num} winner: {winning_code}")
        print(f"  \"{winning_response}\"\n")

    return stats.report()
