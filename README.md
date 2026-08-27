# Kaizen 🤖

A lightweight, fully local AI agent built from scratch in Python — no LangChain, no CrewAI, no agent framework. Just Ollama's API, a message loop, and hand-written tool-calling logic.

Kaizen runs entirely on my own machine against a local LLM (`qwen2.5:3b-instruct` via [Ollama](https://ollama.com)), giving it the ability to read files, list directories, and write files based on natural-language requests — with zero API costs and zero data leaving my computer.

```
 █████   ████   █████████   █████ ███████████ ██████████ ██████   █████
░░███   ███░   ███░░░░░███ ░░███ ░█░░░░░░███ ░░███░░░░░█░░██████ ░░███
 ░███  ███    ░███    ░███  ░███ ░     ███░   ░███  █ ░  ░███░███ ░███
 ░███████     ░███████████  ░███      ███     ░██████    ░███░░███░███
 ░███░░███    ░███░░░░░███  ░███     ███      ░███░░█    ░███ ░░██████
 ░███ ░░███   ░███    ░███  ░███   ████     █ ░███ ░   █ ░███  ░░█████
 █████ ░░████ █████   █████ █████ ███████████ ██████████ █████  ░░█████
░░░░░   ░░░░ ░░░░░   ░░░░░ ░░░░░ ░░░░░░░░░░░ ░░░░░░░░░░ ░░░░░    ░░░░░
```

## Why I built this

I wanted to actually understand how AI agents work under the hood, instead of importing a framework that hides the mechanics. Every line of the core loop — tool detection, dispatch, conversation memory, deduplication — was written and debugged by hand.

## Features

- **Fully local** — runs on Ollama, no API keys, no cloud costs, no data sent anywhere
- **Real tool calling** — the model can read files, list directory contents, and create/write files, using Ollama's native function-calling API
- **Conversation memory** — maintains full context across turns, including tool-call history
- **Duplicate-call protection** — tracks completed tool calls by signature so the model doesn't needlessly re-run the same action
- **Styled terminal UI** — ASCII banner and status panel via [`rich`](https://github.com/Textualize/rich)

## How it works

Kaizen implements the core agent pattern from first principles:

1. The model is given a list of available tools (name, description, JSON-schema parameters)
2. On each turn, the model either replies with plain text, or requests a `tool_call` — a structured request naming a tool and its arguments
3. Python code detects the tool call, looks up the matching function via a dict-based dispatch table, and actually executes it (real file I/O)
4. The tool's result is fed back into the conversation with the proper `tool` role and `tool_call_id`, and the model is called again to produce a real answer grounded in that result

```
User message → Model (Ollama) → tool_call? 
                                    ├── No  → return text answer
                                    └── Yes → run real Python function
                                              → feed result back to model
                                              → call model again
```

## Tools currently available

| Tool | Description |
|---|---|
| `read_file` | Reads and returns the contents of a text file |
| `list_file` | Lists the contents of a directory |
| `write_file` | Creates/writes a file, with optional content |

## Setup

**Requirements:**
- [Ollama](https://ollama.com) installed and running
- Python 3.10+
- A pulled model that supports tool calling (this project uses `qwen2.5:3b-instruct`)

```bash
# Pull the model
ollama pull qwen2.5:3b-instruct

# Install dependencies
pip install requests rich

# Run
python kaizen.py
```

## What I learned building this

Small local models (3B parameters) are genuinely capable of real tool use, but they have real, reproducible quirks worth knowing about if you're building on one:

- **They can hallucinate tool success.** Without a real tool defined for an action, a 3B model will sometimes generate a *plausible-sounding* success message rather than admitting it can't do something — confirmed by checking that no actual `tool_calls` were present in the raw response.
- **They can under-trust their own results.** Even after a tool call genuinely succeeds and the result is fed back correctly, the model sometimes re-issues the same call again rather than trusting the first result — solved here with an explicit dedup guard rather than relying on prompting alone.
- **Message *type* correctness matters a lot.** Ollama's API is strict — `content` must always be a string; passing a list or dict (e.g. a raw file listing) causes a hard server-side error. Every tool now normalizes its return value to a plain string.
- **Windows has a confusing quirk**: attempting to `open()` a directory path (instead of a file path) raises `PermissionError`, not a clearer error — easy to misdiagnose as an actual permissions issue.

## Known limitations

- Only handles one tool call per model turn (no parallel/multi-tool calls yet)
- No sandboxing — the agent has real file system access; use with care
- Small-model tool-calling reliability, while decent, is not perfect

## Roadmap

- [ ] Additional tools (delete file, run shell commands, web fetch)
- [ ] ADD a proper `logging` module usage
- [ ] Generalize the dedup guard to all tools, not just `write_file`

## Tech stack

Python · [Ollama](https://ollama.com) · [`rich`](https://github.com/Textualize/rich) · `qwen2.5:3b-instruct`

---

Built as a hands-on learning project to understand agent architecture from the ground up.
