# mini-claude-code

A small but fully functional agentic coding assistant. You give it a prompt in plain English, and it figures out how to get there by reading files, writing code, and running commands on its own.

I built this as part of the [CodeCrafters "Build Your Own Claude Code" challenge](https://codecrafters.io/challenges/claude-code). This was a super fun challenge. It supported me by explaining how things like the agent loop work and checked my results along the way. It was very easy to get started with and had the perfect mix of challenge and guidance. I would recommend it a lot for everyone who wants to understand how an agent loop works in detail.

---

## How it works

The assistant runs an **agentic loop**:

1. You give it a prompt
2. The model decides what to do next — if it needs more information, it calls a tool (like reading a file or running a command)
3. The tool runs locally and the result goes back to the model
4. This repeats until the model has everything it needs to give a final answer

```
  Your prompt
       |
       v
  [ LLM call ] <------------------------------------+
       |                                            |
       +-- needs a tool --> run it --> send result -+
       |
       +--> print final answer
```

If a tool fails (file not found, command error, etc.), the error is passed back to the model instead of crashing — so it can try a different approach or let you know what went wrong.

---

## What it can do

| Tool | What it does |
|------|-------------|
| `Read` | Read the contents of any file |
| `Write` | Write or overwrite a file |
| `Bash` | Run a shell command and capture the output |

---

## Getting started

You need Python 3.11 or newer. That's it!

```sh
git clone https://github.com/HoergerL/mini-claude-code.git
cd mini-claude-code
pip install -r requirements.txt
```

Then grab a free API key at [openrouter.ai](https://openrouter.ai) and set it:

```sh
# macOS/Linux
export OPENROUTER_API_KEY=your_key_here

# Windows (PowerShell)
$env:OPENROUTER_API_KEY = "your_key_here"
```

---

## Usage

```sh
python -m app.main -p "Your prompt here"
```

### Some things to try

Summarize a file:
```sh
python -m app.main -p "Read README.md and summarize it in one sentence"
```

Chain multiple tools together:
```sh
python -m app.main -p "Read main.py, then write a short summary of what it does to summary.txt"
```

Use bash to explore the environment (Linux/macOS):
```sh
python -m app.main -p "What Python version is installed? Use bash to check."
```

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENROUTER_API_KEY` | — | **Required.** Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API base URL — works with any OpenAI-compatible endpoint |
| `MODEL` | `openrouter/free` | The model to use |

### Choosing a model

The default `openrouter/free` lets OpenRouter automatically pick a capable free model — perfect for getting started. If you want to pin a specific one, check out the [free models with tool support](https://openrouter.ai/models?order=top&supported_parameters=tools&free=1) and set it like this:

```sh
# macOS/Linux
export MODEL="meta-llama/llama-3.3-70b-instruct:free"

# Windows (PowerShell)
$env:MODEL = "meta-llama/llama-3.3-70b-instruct:free"
```

Free models can sometimes return empty responses during high load — the assistant will automatically retry up to 3 times before giving up.

---

## Project structure

```
app/
└── main.py        # Everything: tool definitions, agent loop, tool execution
requirements.txt   # Just one dependency: openai
```

The whole thing is ~190 lines of Python. It's intentionally small and easy to read — great starting point if you want to extend it.

---

## A note on security

The `Bash` tool runs whatever shell command the model asks for — that's what makes it powerful. Just be aware that if the agent reads a malicious file, it could theoretically contain hidden instructions that try to manipulate the model (this is called prompt injection). For personal/local use this is totally fine, but if you run it in a shared or sensitive environment, consider sandboxing it or adding a confirmation step before commands get executed.

