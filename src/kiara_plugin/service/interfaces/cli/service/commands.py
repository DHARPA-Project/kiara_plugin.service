# -*- coding: utf-8 -*-

#  Copyright (c) 2021, University of Luxembourg / DHARPA project
#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)

"""Web-service related subcommands for the cli."""
import typing

import rich_click as click

if typing.TYPE_CHECKING:
    from kiara.api import KiaraAPI


@click.group()
@click.pass_context
def service(ctx):
    """(Web-)service-related sub-commands."""


@service.command()
@click.option(
    "--host", help="The host to bind to.", required=False, default="localhost"
)
@click.option("--port", "-p", help="The port to bind to.", required=False, default=8080)
@click.pass_context
def start(ctx, host: str, port: int):
    """Start a kiara (web) service."""

    from kiara_plugin.service.openapi.service import KiaraOpenAPIService

    try:
        import uvloop

        uvloop.install()
    except Exception:
        pass

    kiara_api: KiaraAPI = ctx.obj.kiara_api

    kiara_service = KiaraOpenAPIService(kiara_api=kiara_api)
    import uvicorn

    app = kiara_service.app()
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config=config)
    server.run()
