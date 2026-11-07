import config
import requests
import tools
from RAGsys import document_search
from rich.console import Console
from rich.rule import Rule
from rich.panel import Panel
import json
import os
from dotenv import load_dotenv
load_dotenv()
model = os.getenv("MODEL")
apikey = os.getenv("API")
import logging 

logger = logging.getLogger(__name__)

console = Console()
KAIZEN = """
 █████   ████   █████████   █████ ███████████ ██████████ ██████   █████
░░███   ███░   ███░░░░░███ ░░███ ░█░░░░░░███ ░░███░░░░░█░░██████ ░░███ 
 ░███  ███    ░███    ░███  ░███ ░     ███░   ░███  █ ░  ░███░███ ░███ 
 ░███████     ░███████████  ░███      ███     ░██████    ░███░░███░███ 
 ░███░░███    ░███░░░░░███  ░███     ███      ░███░░█    ░███ ░░██████ 
 ░███ ░░███   ░███    ░███  ░███   ████     █ ░███ ░   █ ░███  ░░█████ 
 █████ ░░████ █████   █████ █████ ███████████ ██████████ █████  ░░█████
░░░░░   ░░░░ ░░░░░   ░░░░░ ░░░░░ ░░░░░░░░░░░ ░░░░░░░░░░ ░░░░░    ░░░░░ 
                                                                       
                                                                       
                                                                       """
#=====================================database==============================================
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
                    }
                },
                {"type":"function",
                    "function":{
                        "name": "write_file",
                        "description": "Creates a file if doesnt exist in a directory given its path and writes content if provided, Once the task is complete it will return 'Done'",
                        "parameters": {
                            "type": "object",
                            "properties": {
                            "path": {"type": "string", "description": "Full path to the file, including filename and extension (not just the containing folder)"},
                            "content": {"type": "string", "description": "Content to added in the file - OPTIONAL"}
                            },
                        "required": ["path"]
                        }
                    }
                },
                {"type":"function",
                        "function":{
                            "name": "delete_file",
                            "description": "Deletes a file if it exists in a directory given its path, Once the task is completed it will return 'File [path] Deleted Sucessfully'",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                "path": {"type": "string", "description": "Full path to the file, including filename and extension (not just the containing folder)"}
                                },
                            "required": ["path"]
                            }
                        }
                },
                {"type":"function",
                                        "function":{
                                            "name": "search_web",
                                            "description":"The exact topic or question the user wants searched. Only call this tool if the user has specified something concrete to search for — do not invent a topic.",
                                            "parameters": {
                                                "type": "object",
                                                "properties": {
                                                "query": {"type": "string", "description": "Query to search in web"}
                                                },
                                            "required": ["query"]
                                            }
                                        }
                                },
                {"type":"function",
                                        "function":{
                                            "name": "document_search",
                                            "description":"Searches a local document using semantic retrieval and returns the most relevant passages",
                                            "parameters": {
                                                "type": "object",
                                                "properties": {
                                                "query": {"type": "string", "description": "Query to search from document"},
                                                "path": {"type": "string", "description": "Path to file form which the text needs to be extracted for context"}
                                                },
                                            "required": ["query","path"]
                                            }
                                        }
                                }


                ]}
functions= {"read_file":tools.read_file,"list_file":tools.list_file,"write_file":tools.write_file,"delete_file":tools.delete_file,"search_web":tools.search_web,"document_search":document_search}
#=================================================================================================
console.print(KAIZEN,style="blue")
total_tools = len(payload["tools"])
console.print(Panel(f"Yoo gotta type some crazy stuff here...\nfor now there are total {total_tools} Tools/features",title="status",border_style="cyan"))
#========================LLM call=======================================

tset = set()
def qwen(messages: dict):

    logger.info("Model started")   
    response = requests.post(apikey,
                            json={"model": model,
                                "messages": messages["convo"],"tools":messages["tools"],"stream":False})
    logger.debug("Model replied")

    reply = response.json()
    
    if "tool_calls" in reply["message"]:
        payload["convo"].append({"role":"assistant","content":"decided to call a tool","tool_calls":reply["message"]["tool_calls"]})
        tool = reply["message"]["tool_calls"]
        argu = tool[0]["function"]["arguments"]
        name = tool[0]["function"]["name"]

        try:func = functions[name]
        except KeyError:return f"{name}, THIS TOOL DOSE NOT EXIST"
        call_signature = json.dumps({"name": name, "args": argu}, sort_keys=True)        
        if call_signature in tset:
            respon = "This exact task was already completed. Do not repeat it — respond to the user right now. say the task is completed"
        else:
            if "search_web" in name:
                respon = func(argu["query"])
            elif "document_search" in name:
                payload["convo"].append({"role":"system","content":"Instruction: Answer only if the correct answer is stated in the context, if not then say 'I dont know' "})
                respon = func(argu["query"],argu["path"])
                print(respon)
            elif "write_file" in name:
                if argu["content"]:
                    respon = func(argu["path"],argu["content"])
                else:
                    respon = func(argu["path"])
                if "Sucessfully" in respon:
                    tset.add(call_signature)
            else:
                respon = func(argu["path"])
                    
        payload["convo"].append({"role":"tool","tool_call_id":tool[0]["id"],"name":name,"content": respon})
        tool_response = qwen(payload)
        return tool_response
             
    return reply["message"]["content"]
#===============================================================
def main():
    while True:
        console.print(Rule(style="bold cyan"))
        console.print("You: ",style="bold blue",end=" ")
        text = input().strip()
        if text:
            payload["convo"].append({"role":"user","content":text})
            try:
                reply = qwen(payload)
            except Exception:
                console.print(Rule(style="red"))
                console.print("ERROR: LLM DID NOT RESPOND\nPlease Check Your Connection & Try Again",style="bold red",end=" ")
                exit()
            if isinstance(reply, str):
                payload["convo"].append({"role":"assistant","content":reply})
                console.print(Rule(style="blue"))
                console.print(model,": ",style="bold blue",end=" ");print(reply)
            else: print("="*30);print(f"unexpected reply: {reply}")
        else: print("Enter Text")
#==================================================================
    

if __name__ == "__main__":
    main()