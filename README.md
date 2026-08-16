# DebateBench

A multi-LLM debate platform. Anonymized LLM agents debate a topic over
several rounds; each round's winning response becomes shared context for
the next round, while every agent also carries forward its own prior
answer to iterate on.

An orchestrator (a human or a separate judge LLM) picks the winning
response each round. Agents are anonymized with a fresh random code every
round, so the orchestrator never learns which underlying model produced
which response and can't develop a bias toward one.

A separate stats tracker records win counts per agent and only reports
them once the debate ends — it has no other interaction with the debate
pipeline.

## Setup

```bash
uv sync
cp .env.example .env  # fill in API keys for whichever providers you use
```

## Running a debate

```bash
uv run debatebench run configs/example.yaml
```

Agents and the orchestrator are configured via a YAML file. Each agent's
`model` is a [LiteLLM](https://docs.litellm.ai/docs/providers) model
string, so it can point at a hosted API (`gemini/gemini-1.5-flash`,
`gpt-4o-mini`, `claude-3-5-haiku-20241022`, ...) or a local Ollama model
(`ollama/llama3.2:1b`).

## In the browser

```bash
uv run debatebench web                        # opens http://127.0.0.1:7777
uv run debatebench web configs/example.yaml   # prefill the form from a config
uv run debatebench web --port 8000 --no-browser
```

Set the topic, agents and judge in the form, then watch each round arrive
as it happens: the anonymous codes, every argument, and the winner that
carries forward. Real agent names stay hidden until the final standings,
the same guarantee the orchestrator gets.

Choosing `Judged by: Me` puts you in the orchestrator's seat. The run
pauses each round and you click the argument that wins, rather than typing
a code at a prompt.

The page is one viewport with no scrolling: the pipeline diagram on the
left, the arguments on the right, standings along the bottom. Only the
argument column scrolls, and it scrolls itself, so a fullscreen screen
recording never has to move.

The server is standard library only, so nothing is added to the dependency
set for it. Progress reaches the page over Server-Sent Events, and it binds
to `127.0.0.1` — a local tool, not something to expose.

## Deploying the replay

`vercel.json` publishes `src/debatebench/static` as a static site. With no
backend to answer `/api/preset`, the page falls back to replaying
`replay.json`, a real run recorded through the same pipeline. Nothing is
called and no key is needed, which is the point: the live server is not
deployable anyway, since a debate takes minutes of model calls, holds run
state in memory between requests, and streams over a long-lived connection
— none of which survive a serverless function. Publishing it with real keys
would also let anyone spend them.

To record a different run, capture the events from `run_debate`'s
`on_event` hook and write them out as `[{"ev": <event>, "wait": <ms>}, ...]`.

## Docker

```bash
docker build -t debatebench .
docker run --rm --env-file .env -v $(pwd)/configs:/app/configs debatebench configs/example.yaml
```
