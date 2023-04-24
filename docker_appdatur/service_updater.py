import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union


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
        self.repo_dest = Path(repo_dest) if repo_dest else None
        self.server_path = (
            (self.repo_dest / server_name) if self.repo_dest and server_name else None
        )

        if bootstrap:
            self.bootstrap()
        self.pull()

    def _run(
        self, cmd: List[Union[str, Path]], cwd: Optional[Union[str, Path]] = None
    ) -> None:
        _cmd = [str(c) for c in cmd]
        logging.debug(
            "Executing '%(cmd)s' in cwd='%(cwd)s'", {"cmd": " ".join(_cmd), "cwd": cwd}
        )
        subprocess.run(
            cmd,
            cwd=cwd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
        logging.debug(
            "Completed '%(cmd)s' in cwd='%(cwd)s'", {"cmd": " ".join(_cmd), "cwd": cwd}
        )

    def bootstrap(self) -> None:
        logging.info(
            "Bootstrapping %(repo_dest)s",
            {"repo_url": self.repo_url, "repo_dest": self.repo_dest},
        )
        self.clone()

    def clone(self) -> None:
        if self.repo_dest and self.repo_url and not self.repo_dest.exists():
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
        logging.debug(
            "Looking for %(script_name)s in %(server_path)s",
            {"server_path": self.server_path, "script_name": script_name},
        )
        if self.server_path:
            for service_dir_str in os.listdir(self.server_path):
                service_dir = self.server_path / service_dir_str
                logging.debug(
                    "Looking in %(service_dir)s", {"service_dir": service_dir}
                )
                if service_dir.name.startswith(".") or not os.path.isdir(service_dir):
                    continue

                script_path = service_dir / script_name

                if not script_path.is_file():
                    continue

                logging.info(
                    "Running %(script_path)s", {"script_path": str(script_path)}
                )

                self._run([str(script_path)], cwd=str(service_dir))
