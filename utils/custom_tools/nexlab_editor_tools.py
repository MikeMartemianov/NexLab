from smart_agent_arch.tools_loader import export_tool
import subprocess
import sys
import os
import shutil

@export_tool
def create_file(path: str, content: str) -> str:
    """Creates a new file with the specified content relative to the dynamic project.
    :param path: The path where you want to write the file (e.g. project_name/script.py).
    :param content: The exact contents of the file as string.
    """
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File {path} created successfully."
    except Exception as e:
        return f"Error: {e}"

@export_tool
def read_project_file(path: str) -> str:
    """Reads a file to understand what the user has currently written.
    :param path: The file to read.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

@export_tool
def execute_terminal(command: str) -> str:
    """Executes a bash/cmd command in the workspace to test scripts or manage files.
    :param command: The terminal command to execute.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + "\n" + result.stderr
    except Exception as e:
        return f"Error: {e}"
