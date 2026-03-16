import subprocess
import threading

class PersistentPowerShell:
    def __init__(self):
        self.process = subprocess.Popen(
            ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )
        self.lock = threading.Lock()

    def run_command(self, command, timeout=30):
        with self.lock:
            # Write the command and a marker to know when output ends
            marker = "END_OF_COMMAND"
            self.process.stdin.write(command + f"\nWrite-Output '{marker}'\n")
            self.process.stdin.flush()

            output_lines = []
            for line in self.process.stdout:
                if marker in line:
                    break
                output_lines.append(line)
            return "".join(output_lines)

    def close(self):
        with self.lock:
            self.process.stdin.write("exit\n")
            self.process.stdin.flush()
            self.process.terminate()
            self.process.wait()


ps = PersistentPowerShell()

