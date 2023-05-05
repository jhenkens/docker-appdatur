import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union


class ServiceUpdater:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        server_name: Optional[str],
        server_repo_path: Optional[str],
        service_name: Optional[str],
        repo_url: Optional[str],
        repo_dest: Optional[str],
        bootstrap: bool,
        pull_on_start: bool,
        docker_compose_pull: bool,
    ) -> None:
        self.server_name = server_name
        self.service_name = service_name
        self.repo_url = repo_url
        self.repo_dest = None
        self.server_path = None
        if repo_dest:
            self.repo_dest = Path(repo_dest)
            if server_repo_path:
                self.server_path = self.repo_dest / server_repo_path
            elif server_name:
                self.server_path = self.repo_dest / server_name

        self.docker_compose_pull = docker_compose_pull
        if bootstrap:
            self.bootstrap()
        if bootstrap or pull_on_start:
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
            self.compose_pull_up()

    def run_scripts(self, script_name: str) -> None:
        logging.debug(
            "Looking for %(script_name)s in %(server_path)s",
            {"server_path": self.server_path, "script_name": script_name},
        )
        if self.server_path and self.server_path.exists():
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

    def _compose(self, compose_file: Path, args: List[Union[str, Path]]) -> None:
        combined_args: List[Union[str, Path]] = [
            "docker-compose",
            "--project-name",
            f"docker-appdatur-{self.server_name}",
            "--file",
            compose_file,
        ]
        combined_args = combined_args + args
        self._run(combined_args, cwd=compose_file.parent)

    def compose_pull_up(self) -> None:
        if self.repo_dest and self.server_path:
            compose_file = self.server_path / "docker-compose" / "docker-compose.yaml"
            if compose_file.exists():
                if self.docker_compose_pull:
                    logging.debug(
                        "Compose pull on %(compose_file)s",
                        {"compose_file": compose_file},
                    )
                    self._compose(compose_file, ["pull"])

                if self.service_name:
                    logging.debug(
                        "Compose up on %(service_name)s @ %(compose_file)s",
                        {
                            "service_name": self.service_name,
                            "compose_file": compose_file,
                        },
                    )
                    self._compose(compose_file, ["up", "-d", self.service_name])

                logging.debug(
                    "Compose up on %(compose_file)s", {"compose_file": compose_file}
                )
                self._compose(
                    compose_file,
                    ["up", "-d", "--remove-orphans"],
                )
