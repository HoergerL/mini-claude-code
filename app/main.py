import argparse
import os
import sys

from openai import OpenAI
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


def retreive_file_path(tool_arguments: dict) -> str:
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


def execute_tool_read(raw_tool_arguments: str):

    tool_arguments = parse_raw_tool_arguments(raw_tool_arguments)
    file_path = retreive_file_path(tool_arguments)

    f = open(file_path)
    content_file = f.read()
    f.close()

    return content_file


def call_LLM(client: OpenAI, messages: list, tools: dict) -> json:
    response = client.chat.completions.create(
                model="anthropic/claude-haiku-4.5",
                messages=messages,
                tools=[
                    tools
                ]
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
    }

    finish_reason = ""
    while finish_reason != "stop":
        print("calling LLM with message: ", messages)
        llm_response = call_LLM(client, messages, tools)
        print("llm_response: ", llm_response)
        messages.append(llm_response.choices[0].message)

        finish_reason = llm_response.choices[0].finish_reason # either stop or tool_calls

        print("finish_reason: ", finish_reason)

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)

        # print(llm_response.choices)

        if finish_reason == "tool_calls": # meaning it's not the final result, but a tool_call
            print("in finish_reason = tool_calls")
            for tool_call in llm_response.choices[0].message.tool_calls:
                print("in for loop", tool_call)
                tool_call_id = tool_call.id
                tool_name = tool_call.function.name
                raw_tool_arguments = tool_call.function.arguments
                # print("requiring tool call with name ", tool_name, " and arguments ", raw_tool_arguments)

                if tool_name == "Read":
                    tool_response = execute_tool_read(raw_tool_arguments)

                messages.append(
                    {
                        "role": "tool", 
                        "tool_call_id": f"{tool_call_id}",
                        "content": f"{tool_response}"
                    }
                )

        else:
            print(f"unhandled finish_reason {finish_reason}, therefore stopping the execution")

        print("messages: ", messages)

    print(llm_response.choices[0].message.content)

if __name__ == "__main__":
    main()
