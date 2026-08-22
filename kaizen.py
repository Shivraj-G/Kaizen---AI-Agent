import requests
import os

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
                },
                {"type":"function",
                    "function":{
                        "name": "list_file",
                        "description": "lists the files in a directory given its path",
                        "parameters": {
                            "type": "object",
                            "properties": {
                            "path": {"type": "string", "description": "path to the directory"}
                            },
                        "required": ["path"]
                        }
                    }}
                ]}

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
            
            respon = read_file(argu["path"])
            
            payload["convo"].append({"role":"tool","content": respon})
            tool_response = qwen(payload)
            return tool_response
        elif name == "list_file":
            
            respon = list_file(argu["path"])

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

def list_file(path):
    try:
        files = os.listdir(path)
        return ",".join(files)
    except FileNotFoundError:
        return f"{path}, This path does not exist"
    except NotADirectoryError:
        return f"{path}, is not a directory"
    except PermissionError:
        return f"Permision Denied to access {path}"
    except OSError as e:
        return f"OS Error: {e}"

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