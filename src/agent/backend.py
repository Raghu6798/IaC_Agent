from deepagents.backends.protocol import ExecuteResponse, FileUploadResponse, FileDownloadResponse
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.sandbox import BaseSandbox


from openshell.sandbox import SandboxClient, SandboxError

from config.settings import settings

class OpenShellBackend(BaseSandbox):
    def __init__(self, sandbox_name: str):
        self.client = SandboxClient.from_active_cluster()
        
        # Connect to existing or create new
        try:
            self.session = self.client.get_session(sandbox_name)
        except Exception:
            self.session = self.client.create_session()
            self.client.wait_ready(self.session.sandbox.name)
            
    @property
    def id(self) -> str:
        return self.session.sandbox.name

    def execute(self, command: str) -> ExecuteResponse:
        """
        Required by BaseSandbox. 
        All file operations in BaseSandbox will now route through this!
        """
        try:
            # We use /bin/bash -c for compatibility
            cmd_list = ["/bin/bash", "-c", command]
            result = self.session.exec(cmd_list)

            return ExecuteResponse(
                output=result.stdout + result.stderr,
                exit_code=result.exit_code
            )
        except SandboxError as e:
            return ExecuteResponse(output=str(e), exit_code=-1)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Native OpenShell upload implementation."""
        return [self.client.upload_file(self.id, path, content) for path, content in files]

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Native OpenShell download implementation."""
        return [self.client.download_file(self.id, path) for path in paths]

    def close(self):
        self.client.close()


if __name__ == "__main__":
    backend = OpenShellBackend("native-starfish")
    print(backend.execute("ls -la"))