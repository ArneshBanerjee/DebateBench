from collections.abc import Callable

from .agent import Agent
from .anonymizer import assign_codes
from .config import DebateConfig
from .orchestrator import HumanOrchestrator, LLMOrchestrator, Orchestrator
from .stats import StatsTracker

# Called with (event_type, payload) as the debate progresses. The web UI uses
# it to stream a run; the CLI leaves it unset and just prints as before.
EventHook = Callable[[str, dict], None]


def build_orchestrator(config: DebateConfig) -> Orchestrator:
    if config.orchestrator.mode == "llm":
        return LLMOrchestrator(model=config.orchestrator.model)
    return HumanOrchestrator()


def run_debate(
    config: DebateConfig,
    on_event: EventHook | None = None,
    orchestrator: Orchestrator | None = None,
) -> dict[str, int]:
    """Run a debate and return {agent_name: wins}.

    `on_event` receives progress events as the run proceeds. `orchestrator`
    overrides the one implied by the config, which lets a caller pick winners
    some way other than stdin.
    """
    emit = on_event or (lambda _type, _payload: None)

    agents = [Agent(name=a.name, model=a.model) for a in config.agents]
    orchestrator = orchestrator or build_orchestrator(config)
    stats = StatsTracker()

    emit(
        "start",
        {
            "topic": config.topic,
            "rounds": config.rounds,
            "agents": [a.name for a in config.agents],
            "mode": config.orchestrator.mode,
        },
    )

    winning_response: str | None = None
    for round_num in range(1, config.rounds + 1):
        emit("round_start", {"round": round_num})

        # Sequential rather than a comprehension so progress can be reported
        # while the models are still answering.
        responses_by_name: dict[str, str] = {}
        for agent in agents:
            responses_by_name[agent.name] = agent.respond(
                config.topic, round_num, winning_response, config.max_tokens
            )
            emit(
                "agent_done",
                {"round": round_num, "done": len(responses_by_name), "total": len(agents)},
            )

        code_by_name = assign_codes(list(responses_by_name))
        anon_responses = {code: responses_by_name[name] for name, code in code_by_name.items()}

        # Only codes leave this function mid-debate. Names stay behind until
        # the run ends, the same guarantee the orchestrator itself gets.
        emit("responses", {"round": round_num, "responses": anon_responses})

        winning_code = orchestrator.pick_winner(config.topic, round_num, anon_responses)
        winning_name = next(name for name, code in code_by_name.items() if code == winning_code)

        stats.record_win(winning_name)
        winning_response = anon_responses[winning_code]

        emit("winner", {"round": round_num, "code": winning_code})

        print(f"Round {round_num} winner: {winning_code}")
        print(f"  \"{winning_response}\"\n")

    report = stats.report()
    # Safe to attach names now: the mapping can no longer bias a judgement.
    emit("done", {"stats": report})
    return report
