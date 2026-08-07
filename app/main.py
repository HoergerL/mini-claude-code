import argparse
import json
import os
import subprocess

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
MODEL = os.getenv("MODEL", default="google/gemma-4-26b-a4b-it:free")
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "Read",
            "description": "Read and return the contents of a file",
            "parameters": {
                "type": "object",
                "required": ["file_path"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Write",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "required": ["file_path", "content"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to write to"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Bash",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute"
                    }
                }
            }
        }
    }
]


def parse_raw_tool_arguments(raw_tool_arguments: str) -> dict:
    try:
        return json.loads(raw_tool_arguments)
    except json.JSONDecodeError as e:
        raise ValueError(f"failed to parse tool arguments: {e}")


def execute_tool_read(raw_tool_arguments: str) -> str:
    try:
        tool_arguments = parse_raw_tool_arguments(raw_tool_arguments)
        file_path = tool_arguments["file_path"]
    except (ValueError, KeyError) as e:
        return f"Error: {e}"

    try:
        with open(file_path) as f:
            return f.read()
    except OSError as e:
        return f"Error: could not read file '{file_path}': {e}"


def execute_tool_write(raw_tool_arguments: str) -> str:
    try:
        tool_arguments = parse_raw_tool_arguments(raw_tool_arguments)
        file_path = tool_arguments["file_path"]
        content = tool_arguments["content"]
    except (ValueError, KeyError) as e:
        return f"Error: {e}"

    try:
        with open(file_path, "w") as f:
            f.write(content)
        return ""
    except OSError as e:
        return f"Error: could not write file '{file_path}': {e}"


def execute_tool_bash(raw_tool_arguments: str) -> str:
    # NOTE: executes arbitrary shell commands as instructed by the LLM.
    # In production, consider sandboxing or user confirmation for sensitive commands.
    try:
        tool_arguments = parse_raw_tool_arguments(raw_tool_arguments)
        command = tool_arguments["command"]
    except (ValueError, KeyError) as e:
        return f"Error: {e}"

    try:
        result = subprocess.check_output(
            command, shell=True, executable="/bin/bash", stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        result = e.output
    except OSError as e:
        return f"Error: could not execute command: {e}"

    return result.decode("utf-8", errors="replace")


def call_llm(client: OpenAI, messages: list, tools: list):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )

    if not response.choices:
        raise RuntimeError("no choices in response")
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prompt", required=True)
    args = parser.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    messages = [{"role": "user", "content": args.prompt}]
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    while True:
        llm_response = call_llm(client, messages, TOOLS)
        messages.append(llm_response.choices[0].message)

        finish_reason = llm_response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            for tool_call in llm_response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                raw_tool_arguments = tool_call.function.arguments

                if tool_name == "Read":
                    tool_response = execute_tool_read(raw_tool_arguments)
                elif tool_name == "Write":
                    tool_response = execute_tool_write(raw_tool_arguments)
                elif tool_name == "Bash":
                    tool_response = execute_tool_bash(raw_tool_arguments)
                else:
                    tool_response = f"Error: unknown tool '{tool_name}'"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_response
                    }
                )

        elif finish_reason == "stop":
            break
        else:
            raise RuntimeError(f"unhandled finish_reason: {finish_reason}")

    print(llm_response.choices[0].message.content)


if __name__ == "__main__":
    main()
