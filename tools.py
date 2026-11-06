import os
from ddgs import DDGS
import json
from docx import Document
from pdfminer.high_level import extract_text
def read_file(path):
    try:
        if path.endswith(".docx"):
            doc = Document(path)
            full_text = "\n".join(para.text for para in doc.paragraphs)
            return full_text
        elif path.endswith(".pdf"):
            text = extract_text(path)
            return text
        else:
            with open(path, "r") as f:
                return f.read()
    except FileNotFoundError:
        return f"File not found at{path}"
    except PermissionError:
            return f"Permision Denied to access {path}"
    except OSError as e:
            return f"OS Error: {e}"
    except Exception as e:
            return f"Could not read {path}: {e}"

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

def write_file(path,info=None):
    if not os.path.isdir(path):
        try:
            with open(path,"w") as f:
                if info:
                    file = f.write(info)
                    return f"File {path} Created Sucessfully, containing '{info}' ."
                else:
                    file = f.write("")
                    return f"File {path} Created Sucessfully"
        except PermissionError as p:
            return f"Permision Denied to access {path}"
        except OSError as e:
            return f"OS Error: {e}"
    else: return f"{path}, doesnot contain filename, please provide the filename along with the path"

def delete_file(path):
    try:
        os.remove(path)
        return f"File {path} Deleted Sucessfully"
    except FileNotFoundError:
        return f"File {path} Not Found"
    except PermissionError:
        return f"Permision Denied to access {path}"
    except OSError as e:
        return f"OS Error: {e}"

def search_web(query):
    try:    
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if results:
                return json.dumps(results)
            else: return f"No results found for '{query}'"
    except Exception as e:
        return f"Search Failed: {e}"
