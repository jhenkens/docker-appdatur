#! /usr/bin/env python3
import asyncio
import logging
import os
import signal
import sys
from typing import Any

import tornado  # type: ignore
from tornado.web import HTTPError  # type: ignore

from docker_appdatur.github_token_validater import GithubTokenValidater
from docker_appdatur.service_updater import ServiceUpdater

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3


class MainHandler(tornado.web.RequestHandler):
    async def get(self) -> None:
        self.write("Hello, world")


class WebhookHandler(tornado.web.RequestHandler):
    SIGNATURE_HEADER = "x-hub-signature-256"

    def initialize(
        self, token_validator: GithubTokenValidater, service_updater: ServiceUpdater
    ) -> None:
        self.token_validator = token_validator
        self.service_updater = service_updater

    # Test method
    async def get(self) -> None:
        self.service_updater.pull()

    async def post(self) -> None:
        try:
            self.token_validator.verify_signature(
                self.request.body.decode(),
                self.request.headers.get(self.SIGNATURE_HEADER, None),
            )
        except ValueError as value_error:
            raise HTTPError(403) from value_error
        self.service_updater.pull()
        self.write("Good work!")


class TestHashGenerationHandler(tornado.web.RequestHandler):
    def initialize(self, token_validator: GithubTokenValidater) -> None:
        self.token_validator = token_validator

    async def post(self) -> None:
        signature = self.token_validator.generate_signature(self.request.body.decode())
        self.write(signature)


class Server:
    def __init__(self) -> None:
        listen_host = os.getenv("LISTEN_HOST", None)
        self.server_port = int(os.getenv("PORT", "5000"))
        secret_token = os.getenv(
            "SECRET_TOKEN", "5fcf5fa3f302c86aea7af92cd8bf845cb35ded3b"
        )
        token_validator: dict[str, Any] = {
            "token_validator": GithubTokenValidater(secret_token)
        }
        server_name = os.getenv("SERVER_NAME")
        server_repo_path = os.getenv("SERVER_REPO_PATH")
        service_name = os.getenv("APPDATUR_SERVICE_NAME")
        repo_url = os.getenv("REPO_URL")
        repo_dest = os.getenv("REPO_DEST")
        bootstrap = os.getenv("REPO_BOOTSTRAP", "False").lower() == "true"
        pull_on_start = os.getenv("PULL_ON_START", "False").lower() == "true"
        service_updater = ServiceUpdater(
            server_name,
            server_repo_path,
            service_name,
            repo_url,
            repo_dest,
            bootstrap,
            pull_on_start,
        )
        application = tornado.web.Application(
            [
                (r"/", MainHandler),
                (r"/generate", TestHashGenerationHandler, token_validator),
                (
                    r"/webhook",
                    WebhookHandler,
                    {**token_validator, "service_updater": service_updater},
                ),
            ],
            default_host=listen_host,
        )
        self.server = tornado.httpserver.HTTPServer(application)
        self.event = asyncio.Event()

    async def run(self) -> None:
        logging.info("Started!")
        self.server.listen(self.server_port)
        try:
            await self.event.wait()
        except asyncio.CancelledError:
            await self.stop("CancelledError")

    async def stop(self, signame: str) -> None:  # pylint: disable=redefined-outer-name
        logging.info("Received %(signame)s... Shutting down...", {"signame": signame})
        self.server.stop()
        await asyncio.wait_for(self.server.close_all_connections(), timeout=5)
        self.event.set()


if __name__ == "__main__":
    LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)]
    )

    server = Server()

    loop = asyncio.get_event_loop()
    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(
            getattr(signal, signame),
            lambda signame=signame: asyncio.create_task(server.stop(signame)),
        )
    loop.run_until_complete(server.run())
