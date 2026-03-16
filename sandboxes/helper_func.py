from contextlib import asynccontextmanager
from datetime import timedelta
from code_interpreter import CodeInterpreter, SupportedLanguage
from opensandbox import Sandbox
from opensandbox.models import WriteEntry

@asynccontextmanager
async def sandbox_context(timeout_minutes: int = 10, python_version: str = "3.11"):
    sandbox = await Sandbox.create(
        "opensandbox/code-interpreter:v1.0.1",
        entrypoint=["/opt/opensandbox/code-interpreter.sh"],
        env={"PYTHON_VERSION": python_version},
        timeout=timedelta(minutes=timeout_minutes),
    )
    
    try:
        async with sandbox:
            code_interpreter = await CodeInterpreter.create(sandbox)
            # Yielding both sandbox and code_interpreter so you can run commands/files directly on the sandbox
            yield sandbox, code_interpreter
    finally:
        await sandbox.kill()

