import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union, IO


class ServiceUpdater:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        server_name: str,
        server_repo_path: str,
        service_name: str,
        compose_file_name: str,
        repo_url: str,
        repo_dest: str,
        bootstrap: bool,
        pull_on_start: bool,
        docker_compose_pull: bool,
        bootstrap_compose_file_name: Optional[str],
    ) -> None:
        self.server_name = server_name
        self.service_name = service_name
        self.repo_url = repo_url
        self.repo_dest = None
        self.server_path = None
        self.repo_dest = Path(repo_dest)
        self.server_path = self.repo_dest / server_repo_path

        self.docker_compose_pull = docker_compose_pull

        self.compose_file = self.server_path / "docker-compose" / compose_file_name
        self.bootstrap_compose_file = None
        if bootstrap_compose_file_name:
            self.bootstrap_compose_file = (
                self.server_path / "docker-compose" / bootstrap_compose_file_name
            )
        self.compose_project_name = f"docker-appdatur-{self.server_name}"
        self.bootstrap_compose_project_name = (
            f"docker-appdatur-{self.server_name}-bootstrap"
        )

        if bootstrap:
            self.bootstrap()
        if bootstrap or pull_on_start:
            self.pull()

    def _run(
        self,
        cmd: List[Union[str, Path]],
        cwd: Optional[Union[str, Path]] = None,
        check: bool = True,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        _cmd = [str(c) for c in cmd]
        logging.debug(
            "Executing '%(cmd)s' in cwd='%(cwd)s'", {"cmd": " ".join(_cmd), "cwd": cwd}
        )
        stdout: None | IO = sys.stdout
        stderr: None | IO = sys.stderr
        if capture_output:
            stdout, stderr = (None, None)
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=stdout,
            stderr=stderr,
            capture_output=capture_output,
            check=check,
        )
        logging.debug(
            "Completed '%(cmd)s' in cwd='%(cwd)s'", {"cmd": " ".join(_cmd), "cwd": cwd}
        )
        return result

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

    def _compose(
        self,
        compose_file: Path,
        args: List[Union[str, Path]],
        project_name: Optional[str] = None,
        dry_run: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        if project_name is None:
            project_name = self.compose_project_name
        combined_args: List[Union[str, Path]] = [
            "docker",
            "compose",
            "--project-name",
            project_name,
            "--file",
            compose_file,
        ]
        if dry_run:
            combined_args = combined_args + ["--dry-run", "--"]
        combined_args = combined_args + args
        return self._run(combined_args, cwd=compose_file.parent, capture_output=dry_run)

    def bootstrap_compose_down(self) -> None:
        if self.bootstrap_compose_file and self.bootstrap_compose_file.exists():
            logging.debug("Running compose-down on boostrap stack")
            self._compose(
                self.bootstrap_compose_file,
                ["down"],
                project_name=self.bootstrap_compose_project_name,
            )

    def changes_for_self(self, compose_file: Path) -> bool:
        logging.debug("Dry run compose for self")
        compose_self_args: list[Union[str, Path]] = ["up", "-d", self.service_name]
        dry_run = self._compose(compose_file, compose_self_args, dry_run=True)
        output = dry_run.stdout.decode("utf-8")
        logging.debug(
            "Dry run output: \n%(dry_run_output)s", {"dry_run_output": output}
        )
        output = [
            x for x in output.split("\n") if f"Container {self.service_name}" in x
        ][0]
        return not "Running" in output

    def bootstrap_self_update(self) -> None:
        logging.debug("Starting a new bootstrap to update this stack, then ending.")
        if self.bootstrap_compose_file and self.bootstrap_compose_file.exists():
            self._compose(
                self.bootstrap_compose_file,
                ["up", "-d"],
                project_name=self.bootstrap_compose_project_name,
            )

    def broken_self_update(self) -> None:
        compose_file = self.compose_file
        logging.debug(
            "We need to update ourself, but we are going to cause the stack to go down. Please manually intervene"
        )
        logging.debug(
            "Compose up on %(service_name)s @ %(compose_file)s",
            {
                "service_name": self.service_name,
                "compose_file": compose_file,
            },
        )
        compose_self_args: list[Union[str, Path]] = ["up", "-d", self.service_name]
        self._compose(compose_file, compose_self_args)

    def compose_pull_up(self) -> None:
        self.bootstrap_compose_down()

        compose_file = self.compose_file
        if compose_file.exists():
            if self.docker_compose_pull:
                logging.debug(
                    "Compose pull on %(compose_file)s",
                    {"compose_file": compose_file},
                )
                self._compose(compose_file, ["pull"])

            if self.service_name:
                if self.changes_for_self(compose_file):
                    logging.debug("Going to update %(service_name).")
                    if self.bootstrap_compose_file:  # pylint: disable=no-else-return
                        self._compose(compose_file, ["pull", self.service_name])
                        self.bootstrap_self_update()
                        return  # fast - exit
                    else:
                        self.broken_self_update()

            logging.debug(
                "Compose up on %(compose_file)s", {"compose_file": compose_file}
            )
            self._compose(
                compose_file,
                ["up", "-d", "--remove-orphans"],
            )
