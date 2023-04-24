import os
import sys
import subprocess
from typing import Optional


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
        if repo_dest and repo_url and bootstrap and not os.path.exists(repo_dest):
            subprocess.run(
                ["git", "clone", repo_url, repo_dest],
                stdout=sys.stdout,
                stderr=sys.stderr,
                check=True,
            )
