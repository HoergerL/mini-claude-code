import argparse
import os
import sys

from openai import OpenAI
import json

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

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

    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=[{"role": "user", "content": args.p}],
        tools=[
            tools
        ]
    )

    if not chat.choices or len(chat.choices) == 0:
        raise RuntimeError("no choices in response")


    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    print(chat.choices)

    if chat.choices[0].finish_reason == "tool_calls": # meaning it's not the final result, but a tool_call
        tool_name = chat.choices[0].message.tool_calls[0].function.name
        raw_tool_arguments = chat.choices[0].message.tool_calls[0].function.arguments
        print("requiring tool call with name ", tool_name, " and arguments ", raw_tool_arguments)

        if tool_name == "Read":
            try: 
                tool_arguments = json.loads(raw_tool_arguments)
            except Exception as e:
                print(f"the tool_arguemnts couldn't be parsed as json. Given Input: {raw_tool_arguments}, Error details {e}")
                exit(1)

        print("cleaned tool arguments : ", tool_arguments)
        if len(tool_arguments) != 1:
            print("The tool_arguments need to only contain a file_path argument")
            exit(1)

        try:
            file_path = tool_arguments['file_path']
        except Exception as e:
            print("The tool_arguments does't contain a file_path argument")
            exit(1)

        print("file_path: ", file_path)

        f = open(file_path)
        content_file = f.read()
        f.close()

        print(content_file)

    else:
    # TODO: Uncomment the following line to pass the first stage
        print(chat.choices[0].message.content)


if __name__ == "__main__":
    main()
