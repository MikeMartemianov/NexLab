import subprocess
from pathlib import Path
from smart_agent_arch.tools_loader import export_tool

@export_tool
def check_python_syntax(file_path: str) -> str:
    """
    Checks the syntax of a Python file using py_compile (standard library).
    This is extremely useful for CoderAgent to verify code correctness before confirming.
    
    :param file_path: Absolute or relative path to the Python file.
    :return: 'Syntax OK' or the compilation error string.
    """
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"
        
    try:
        # Run python -m py_compile to check syntax without execution
        result = subprocess.run(["python", "-m", "py_compile", str(path)], 
                              capture_output=True, text=True)
                              
        if result.returncode == 0:
            return "Syntax OK. The file has no parse errors."
        else:
            return f"Syntax Error Found:\n{result.stderr}"
    except Exception as e:
        return f"Could not run syntax check: {str(e)}"
