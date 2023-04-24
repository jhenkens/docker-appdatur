import os
from pathlib import Path
import sys
import subprocess
from typing import List, Optional


class ServiceUpdater:
    def __init__(
        self,
        server_name: Optional[str],
        repo_url: Optional[str],
        repo_dest: Optional[str],
        bootstrap: bool,
    ) -> None:
        self.server_name = server_name
        self.repo_url = repo_url
        self.repo_dest = repo_dest
        self.server_path = None
        if repo_dest and server_name:
            self.server_path = str(Path(repo_dest) / server_name)

        if repo_dest and repo_url and bootstrap and not os.path.exists(repo_dest):
            self.clone()
        self.pull()

    def _run(self, cmd: List[str], cwd: Optional[str] = None) -> None:
        subprocess.run(
            cmd,
            cwd=cwd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )

    def clone(self) -> None:
        if self.repo_dest and self.repo_url and not os.path.exists(self.repo_dest):
            self._run(
                ["git", "clone", self.repo_url, self.repo_dest],
            )

    def pull(self) -> None:
        if self.repo_dest:
            self._run(
                ["git", "pull", "--ff-only"],
                cwd=self.repo_dest,
            )
            self.run_scripts("after_pull.sh")

    def run_scripts(self, script_name: str) -> None:
        if self.server_path:
            for service_dir in os.listdir(self.server_path):
                if service_dir.startswith(".") or not os.path.isdir(service_dir):
                    continue
                script_path = str(Path(service_dir) / script_name)
                if not os.path.isfile(script_path):
                    continue
                self._run([script_path], cwd=service_dir)
