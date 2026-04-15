import subprocess
import threading
import os
from langchain_core.tools import tool
from utils.ui import show_info, show_error

@tool
def run_shell_commands(command: str, cwd: str = None, timeout: int = 60) -> str:
    """
    Executes a shell command, streams and logs output/errors, and returns the combined logs as a string.
    LLM: Always invoke this tool directly when the user requests shell or git commands. Do NOT ask for permission or confirmation from the user.
    Args:
        command (str): The shell command to execute.
        cwd (str, optional): The working directory to run the command in.
        timeout (int, optional): Maximum time to wait for the command (seconds).
    Returns:
        str: Combined output and error logs.
    """
    try:
        show_info(f"Running shell command: {command} in {cwd or os.getcwd()}")
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        logs = []

        def read_logs():
            for line in process.stdout:
                if "ERROR" in line or "Traceback" in line:
                    show_error(line.rstrip())
                elif "CRITICAL" in line:
                    show_error(line.rstrip())
                elif "WARNING" in line:
                    show_info(line.rstrip())
                elif "DEBUG" in line:
                    show_info(line.rstrip())
                else:
                    show_info(line.rstrip())
                logs.append(line)

        t = threading.Thread(target=read_logs)
        t.start()
        t.join(timeout=timeout)
        process.terminate()
        process.wait()
        show_info(f"Shell command execution completed: {command}")
        return "".join(logs)
    except Exception as e:
        show_error(f"Exception occurred while running shell command '{command}': {e}")
        return f"Exception occurred while running shell command '{command}': {e}"
