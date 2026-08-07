# mini-claude-code

A minimal agentic coding assistant powered by an LLM. Give it a natural language prompt and it will autonomously read files, write files, and execute shell commands to complete the task.

Built as part of the [CodeCrafters "Build Your Own Claude Code" challenge](https://codecrafters.io/challenges/claude-code) — a fantastic challenge that walks you through implementing an LLM-powered coding agent from scratch. Highly recommended if you want to understand how tools like Claude Code actually work under the hood.

---

## How it works

The assistant runs an agentic loop:

1. Sends your prompt to the LLM
2. If the model requests a tool call (`Read`, `Write`, or `Bash`), executes it and feeds the result back
3. Repeats until the model produces a final answer (`finish_reason: stop`)

```
User prompt → LLM → tool call? → execute tool → LLM → ... → final answer
```

## Tools

| Tool | Description |
|------|-------------|
| `Read` | Read the contents of a file |
| `Write` | Write content to a file |
| `Bash` | Execute a shell command |

## Setup

**Prerequisites:** Python 3.11+, [uv](https://github.com/astral-sh/uv)

```sh
git clone https://github.com/HoergerL/mini-claude-code.git
cd mini-claude-code
```

Set your API key (uses [OpenRouter](https://openrouter.ai) by default):

```sh
export OPENROUTER_API_KEY=your_key_here
```

## Usage

```sh
uv run -m app.main -p "Your prompt here"
```

**Example:**

```sh
uv run -m app.main -p "Read README.md and summarize it in one sentence"
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Required. Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API base URL (compatible with any OpenAI-compatible endpoint) |

The model is set to `anthropic/claude-haiku-4.5` in `app/main.py` and can be changed there.

## Security note

The `Bash` tool executes arbitrary shell commands as instructed by the LLM. In production, consider running inside a sandbox or adding user confirmation for sensitive commands.
2. Run `./your_program.sh` to run your program, which is implemented in
   `app/main.py`.
3. Run `codecrafters submit` to submit your solution to CodeCrafters. Test
   output will be streamed to your terminal.
