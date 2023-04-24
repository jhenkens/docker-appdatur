import logging
import os
import subprocess
import sys
from pathlib import Path
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

        if bootstrap:
            self.bootstrap()
        self.pull()

    def _run(self, cmd: List[str], cwd: Optional[str] = None) -> None:
        logging.debug(
            "Executing '%(cmd)s' in cwd='%(cwd)s'", {"cmd": " ".join(cmd), "cwd": cwd}
        )
        subprocess.run(
            cmd,
            cwd=cwd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
        logging.debug(
            "Completed '%(cmd)s' in cwd='%(cwd)s'", {"cmd": " ".join(cmd), "cwd": cwd}
        )

    def bootstrap(self) -> None:
        logging.info(
            "Bootstrapping %(repo_dest)s",
            {"repo_url": self.repo_url, "repo_dest": self.repo_dest},
        )
        self.clone()

    def clone(self) -> None:
        if self.repo_dest and self.repo_url and not os.path.exists(self.repo_dest):
            logging.info(
                "Pulling %(repo_url)s to %(repo_dest)s",
                {"repo_url": self.repo_url, "repo_dest": self.repo_dest},
            )
            self._run(
                ["git", "clone", self.repo_url, self.repo_dest],
            )

    def pull(self) -> None:
        if self.repo_dest:
            logging.info(
                "Pulling %(repo_dest)s",
                {"repo_dest": self.repo_dest},
            )
            self._run(
                ["git", "pull", "--ff-only"],
                cwd=self.repo_dest,
            )
            self.run_scripts("after_pull.sh")

    def run_scripts(self, script_name: str) -> None:
        logging.debug("Looking for %s(server_path)", {"server_path": self.server_path})
        if self.server_path:
            for service_dir_str in os.listdir(self.server_path):
                logging.debug(
                    "Looking in %s(service_dir)", {"service_dir": service_dir_str}
                )
                service_dir = Path(service_dir_str)
                if service_dir.name.startswith(".") or not os.path.isdir(service_dir):
                    continue
                script_path = service_dir / script_name
                if not script_path.is_file():
                    continue
                logging.info(
                    "Running %(script_path)s", {"script_path": str(script_path)}
                )
                self._run([str(script_path)], cwd=str(service_dir))
