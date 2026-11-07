# Kaizen 🤖

A lightweight, fully local AI agent built from scratch in Python — no LangChain, no CrewAI, no agent framework. Just Ollama's API, a message loop, hand-written tool calling, and a from-scratch RAG pipeline.

Kaizen runs entirely on my own machine against a local LLM (`qwen2.5:3b-instruct` via [Ollama](https://ollama.com)). It can read, list, write and delete files, search the web, and answer questions about my own documents (`.txt`, `.docx`, `.pdf`) — with zero API costs and no document data leaving my computer.

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

I wanted to actually understand how AI agents work under the hood, instead of importing a framework that hides the mechanics. Every piece — the tool-calling loop, dispatch, conversation memory, deduplication, chunking, embeddings, retrieval and the evaluation harness — was written and debugged by hand. I first started this because i just wanted to use an AI Agent locally on my low-end laptop, but Agent harness like Hermes and others were not compatible with small models which fit into my laptop, so i decided to build my own from scratch. 
## Features

- **Fully local** — runs on Ollama, no API keys, no cloud costs
- **Real tool calling** — the model can read, list, write and delete files and search the web, using Ollama's native function-calling API
- **Document Q&A (RAG)** — ask questions about a `.txt`, `.docx` or `.pdf` file; relevant passages are retrieved by meaning (embeddings + cosine similarity) and handed to the model as context
- **Measured, not guessed** — retrieval settings were chosen from a 48-configuration sweep against a 13-question eval set (see [Evaluating retrieval](#evaluating-retrieval))
- **Conversation memory** — full context across turns, including tool-call history
- **Duplicate-call protection** — tracks completed tool calls by signature so the model doesn't needlessly re-run the same action
- **Styled terminal UI** — ASCII banner and status panel via [`rich`](https://github.com/Textualize/rich)

## How it works

Kaizen implements the core agent pattern from first principles:

1. The model is given a list of available tools (name, description, JSON-schema parameters)
2. On each turn, the model either replies with plain text, or requests a `tool_call` — a structured request naming a tool and its arguments
3. Python code detects the tool call, looks up the matching function via a dict-based dispatch table, and actually executes it (real file I/O, a real web search, a real retrieval)
4. The tool's result is fed back into the conversation with the proper `tool` role and `tool_call_id`, and the model is called again to produce an answer grounded in that result

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
| `read_file` | Reads a file and returns its text (supports `.txt`, `.docx`, `.pdf`) |
| `list_file` | Lists the contents of a directory |
| `write_file` | Creates/writes a file, with optional content |
| `delete_file` | Deletes a file |
| `search_web` | Searches the web (DuckDuckGo) and returns the top 5 results |
| `search_document` | RAG: retrieves the most relevant passages from a local document for a query |

## Document search (RAG)

The RAG pipeline is built from raw HTTP calls and `numpy` — no vector database or framework.

```
document ──► read (txt / docx / pdf)
         ──► split into overlapping word chunks
         ──► embed each chunk (nomic-embed-text, 768 dims, via Ollama)
query    ──► embed the query
         ──► cosine similarity against every chunk
         ──► take the top-n chunks
         ──► put them in the prompt as context, before the question
         ──► model answers from that context
```

Defaults, chosen from the sweep below: `chunk_size=150` words, `overlap=15`, `top_n=2`.

## Evaluating retrieval

Instead of tuning by eyeballing answers, I built a small eval harness.

**Setup:** a 1,211-word document (a Wikipedia-style article on the history of psychology) and 13 factual questions, each with a short expected answer string that appears verbatim in the document (e.g. *"Who is the earliest known English user of the word 'psychology'?" → "Blankaart"*). A question counts as a retrieval hit if the expected string appears in any of the top-n retrieved chunks. Questions are worded differently from the source text so they test retrieval by meaning, not keyword overlap.

**Sweep:** chunk size 100 / 150 / 200 / 300 words × overlap 10 / 15 / 20 / 25 × top_n 1 / 2 / 3 = 48 configurations. Hits out of 13, shown as the range across the four overlaps:

| chunk_size | top_n=1 | top_n=2 | top_n=3 |
|---|---|---|---|
| 100 | 11–12 | 12–13 | 12–13 |
| 150 | 10–12 | 11–13 | 11–13 |
| 200 | 8–9 | 10–13 | 12–13 |
| 300 | 6–8 | 10–12 | 10–13 |

**What it showed:**

- **Smaller chunks win at `top_n=1`.** Hit rate falls steadily as chunks grow (about 11 at 100 words, 6–8 at 300). Large chunks blend several topics into one embedding, so the single best chunk is often the wrong one.
- **Big chunks need a bigger `top_n` to compensate, which costs context.** 300-word chunks at `top_n=3` send about 900 words to the model; 100–150-word chunks at `top_n=2` reach 13/13 with 200–300 words.
- **Overlap results are noisy.** With 13 questions, one question is worth about 8 points, and changing overlap mostly just moves where the chunk boundaries land. I chose `150 / 15 / 2` because its neighbouring overlaps (10 and 20) also score 13/13 — a stable region, not a lucky cell.
- **Near misses had a cause.** Two questions initially failed because look-alike chunks outranked the right one: a sentence about "Professor of *Empirical Psychology*" beat the one about the book *Psychologia Empirica*, and a passage mentioning "experimentation" beat a buried sentence about Kant rejecting experimental psychology. Embeddings match topic similarity, not exact names.

**Caveats (honest ones):** the settings were tuned on the same 13 questions, so they are partly fitted; the document is small; and this measures *retrieval only*, not whether the model's final answer is correct. Answer-level and held-out evals are next (see roadmap).

## Setup

**Requirements:**
- [Ollama](https://ollama.com) installed and running
- Python 3.10+
- Two pulled models: a chat model that supports tool calling, and an embedding model

```bash
# Pull the models
ollama pull qwen2.5:3b-instruct
ollama pull nomic-embed-text

# Install dependencies
pip install requests rich numpy python-dotenv ddgs python-docx pdfminer.six
```

Create a `.env` file next to the scripts:

```
API=http://localhost:11434/api/chat
EmbedAPI=http://localhost:11434/api/embeddings
MODEL=qwen2.5:3b-instruct
```

```bash
# Run the agent
python kaizen.py
```

## Project structure

| File | Purpose |
|---|---|
| `kaizen.py` | Agent loop, tool dispatch, conversation memory, terminal UI |
| `tools.py` | Tool implementations (file operations, web search, file readers) |
| `RAGsys.py` | RAG pipeline (embedding, chunking, retrieval) and the evaluation harness |

## What I learned building this

Small local models (3B parameters) are genuinely capable of real tool use and RAG, but they have real, reproducible quirks:

- **They can hallucinate tool success.** Without a real tool defined for an action, a 3B model will sometimes generate a *plausible-sounding* success message rather than admitting it can't do something — confirmed by checking that no actual `tool_calls` were present in the raw response.
- **They can under-trust their own results.** Even after a tool call succeeds and the result is fed back correctly, the model sometimes re-issues the same call — handled with an explicit dedup guard rather than relying on prompting alone.
- **They invent arguments.** Asked a vague *"can you browse the web?"*, the model searched for a topic it made up. Tightening the tool schema description ("only call this if the user gave a concrete topic — do not invent one") made it ask for a query instead. Schema wording changes behaviour.
- **Message *type* correctness matters.** Ollama's API is strict — `content` must always be a string; passing a list or dict (e.g. a raw file listing or search results) causes a hard server-side error. Every tool normalizes its return value to a string.
- **Windows has a confusing quirk**: `open()` on a directory path raises `PermissionError`, not a clearer error — easy to misdiagnose as a real permissions problem.
- **A `.docx` is not a text file.** It is a zip of XML, so `open(path).read()` fails with decode errors no matter the encoding; it needs a dedicated parser.
- **Chunk size is a real design lever.** 20-word chunks gave disconnected fragments; 300-word chunks blurred topics together. The sweep above found the middle.
- **Debug the measurement before the system.** My first eval run scored 3/13 — the cause was a case-sensitive comparison in the eval itself, not retrieval. After fixing it the score jumped to 11/13, and the two remaining misses turned out to be look-alike chunks (see above).
- **`logging` at DEBUG level also shows library chatter.** Setting the root logger to DEBUG printed every HTTP connection from `urllib3`; library loggers need their own level.

## Known limitations

- Only handles one tool call per model turn (no parallel tool calls yet)
- No sandboxing — the agent has real file system access, including delete; use with care
- `search_document` re-reads and re-embeds the whole document on every query (about 2 seconds per chunk on my CPU); there is no persistence or caching yet
- Retrieval is evaluated, but final-answer quality and "I don't know" behaviour are not yet
- Small-model reliability, while decent, is not perfect

## Roadmap

- [x] Web search tool
- [x] Document search (RAG) over `.txt` / `.docx` / `.pdf`
- [x] Delete-file tool
- [x] Retrieval eval harness and chunk-size / overlap / top-n sweep
- [ ] Answer-level eval, including questions the document doesn't answer (the model should say it doesn't know)
- [ ] Held-out question set to check the tuned settings generalize
- [ ] Cache embeddings to disk so documents aren't re-embedded on every query
- [ ] Paragraph-aware chunking
- [ ] Hybrid search (keyword + embeddings) for exact names and titles
- [ ] Vector database (e.g. Chroma), measured against the eval
- [ ] Shell command tool (with safety limits)
- [ ] Generalize the dedup guard to all tools
- [ ] Finish moving the remaining debug prints to the `logging` module (the eval harness already uses it)

## Tech stack

Python · [Ollama](https://ollama.com) · `qwen2.5:3b-instruct` · `nomic-embed-text` · `numpy` · [`rich`](https://github.com/Textualize/rich) · `ddgs` · `python-docx` · `pdfminer.six`

---

Built as a hands-on learning project to understand agent and retrieval architecture from the ground up.
