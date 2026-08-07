import argparse
import os
import sys

from openai import OpenAI
import subprocess
import json

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def parse_raw_tool_arguments(raw_tool_arguments: str) -> dict:
    try: 
        tool_arguments = json.loads(raw_tool_arguments)
    except Exception as e:
        print(f"the tool_arguemnts couldn't be parsed as json. Given Input: {raw_tool_arguments}, Error details {e}")
        exit(1)

    # print("cleaned tool arguments : ", tool_arguments)

    return tool_arguments


def retreive_read_parameter(tool_arguments: dict) -> str:
    if len(tool_arguments) != 1:
        print("The tool_arguments need to only contain a file_path argument")
        exit(1)
    # print("file_path: ", file_path)
    try:
        file_path = tool_arguments['file_path']
    except Exception as e:
        print("The tool_arguments does't contain a file_path argument")
        exit(1)

    return file_path

def retreive_write_parameters(tool_arguments: dict) -> tuple:
    if len(tool_arguments) != 2:
        print("The tool_arguments need to contain a file_path and a content argument")
        exit(1)
    # print("file_path: ", file_path)
    try:
        file_path = tool_arguments['file_path']
        content = tool_arguments['content']
    except Exception as e:
        print("The tool_arguments does't contain a file_path or a content argument")
        exit(1)

    return (file_path, content)


def retreive_bash_parameter(tool_arguments: dict) -> str:
    if len(tool_arguments) != 1:
            print("The tool_arguments need to only contain a command argument")
            exit(1)
    # print("file_path: ", file_path)
    try:
        command = tool_arguments['command']
    except Exception as e:
        print("The tool_arguments does't contain a command argument")
        exit(1)

    return command


def execute_tool_read(raw_tool_arguments: str) -> str:

    tool_arguments = parse_raw_tool_arguments(raw_tool_arguments)
    file_path = retreive_read_parameter(tool_arguments)

    f = open(file_path)
    content_file = f.read()
    f.close()

    return content_file


def execute_tool_write(raw_tool_arguments: str) -> None:
    tool_arguments = parse_raw_tool_arguments(raw_tool_arguments)
    file_path, content = retreive_write_parameters(tool_arguments)

    f = open(file_path, "w")
    f.write(content)
    f.close()

def execute_tool_bash(raw_tool_arguments: str) -> str:
    tool_arguments = parse_raw_tool_arguments(raw_tool_arguments)
    command = retreive_bash_parameter(tool_arguments)

    
    try:
        result = subprocess.check_output(command, shell = True, executable = "/bin/bash", stderr = subprocess.STDOUT)

    except subprocess.CalledProcessError as cpe:
        result = cpe.output

    return result.decode("utf-8", errors="replace")



def call_LLM(client: OpenAI, messages: list, tools: list) -> json:
    response = client.chat.completions.create(
                model="anthropic/claude-haiku-4.5",
                messages=messages,
                tools=tools
            )
    
    if not response.choices or len(response.choices) == 0:
        raise RuntimeError("no choices in response")
    return response



def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True) # p = prompt
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    messages = [{"role": "user", "content": args.p}]
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    tools = \
    [
        {
            "type": "function",
            "function": {
                "name": "Read",
                "description": "Read and return the contents of a file",
                "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                    "type": "string",
                    "description": "The path to the file to read"
                    }
                },
                "required": ["file_path"]
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

    while True:
        llm_response = call_LLM(client, messages, tools)
        messages.append(llm_response.choices[0].message)

        finish_reason = llm_response.choices[0].finish_reason # either stop or tool_calls

        # print("finish_reason: ", finish_reason)

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)

        # print(llm_response.choices)

        if finish_reason == "tool_calls": # meaning it's not the final result, but a tool_call
            for tool_call in llm_response.choices[0].message.tool_calls:
                tool_call_id = tool_call.id
                tool_name = tool_call.function.name
                raw_tool_arguments = tool_call.function.arguments
                # print("requiring tool call with name ", tool_name, " and arguments ", raw_tool_arguments)

                if tool_name == "Read":
                    tool_response = execute_tool_read(raw_tool_arguments)
                if tool_name == "Write":
                    execute_tool_write(raw_tool_arguments)
                    tool_response = "" # write doesn't return a response
                if tool_name == "Bash":
                    tool_response = execute_tool_bash(raw_tool_arguments)

                messages.append(
                    {
                        "role": "tool", 
                        "tool_call_id": f"{tool_call_id}",
                        "content": f"{tool_response}"
                    }
                )

        elif finish_reason == "stop":
            break
        else:
            raise RuntimeError(f"unhandled finish_reason: {finish_reason}")


    print(llm_response.choices[0].message.content)

if __name__ == "__main__":
    main()
