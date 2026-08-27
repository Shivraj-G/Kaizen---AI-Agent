import os

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found at{path}"
    except PermissionError:
            return f"Permision Denied to access {path}"
    except OSError as e:
            return f"OS Error: {e}"

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
                else:
                    file = f.write("")
                return "DONE"
        except PermissionError as p:
            return f"Permision Denied to access {path}"
        except OSError as e:
            return f"OS Error: {e}"
    else: return f"{path}, doesnot contain filename, please provide the filename along with the path"