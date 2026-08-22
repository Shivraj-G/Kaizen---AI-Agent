import requests

payload = {"convo":[],"tools":[{"type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "description": "Reads the contents of a text file given its path",
                                        "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "path": {"type": "string", "description": "path to the file"}
                                        },
                                        "required": ["path"]
                                        }
                                    }
                }]}

def qwen(messages: dict):
    
    response = requests.post("http://localhost:11434/api/chat",
                             json={"model": "qwen2.5:3b-instruct",
                                   "messages": messages["convo"],"tools":messages["tools"],"stream":False})

    reply = response.json()
    if "tool_calls" in reply["message"]:
        tool = reply["message"]["tool_calls"]
        argu = tool[0]["function"]["arguments"]
        name = tool[0]["function"]["name"]
        if name == "read_file":
            print(f"[DEBUG] Model wants to read: {argu['path']!r}")
            respon = read_file(argu["path"])
            print(f"[DEBUG] read_file returned: {respon!r}")
            payload["convo"].append({"role":"tool","content": respon})
            tool_response = qwen(payload)
            return tool_response
            

    return reply["message"]["content"]

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found at{path}"

def main():
    while True:
        text = input("type: ").strip()
        if text:
            payload["convo"].append({"role":"user","content":text})
            reply = qwen(payload)
            if isinstance(reply, str):
                payload["convo"].append({"role":"assistant","content":reply})
                print(reply)
            else: print("="*30);print(f"unexpected reply: {reply}")
        else: print("Enter Text")

    

if __name__ == "__main__":
    main()