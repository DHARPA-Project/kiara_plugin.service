# -*- coding: utf-8 -*-

#  Copyright (c) 2021, University of Luxembourg / DHARPA project
#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)

"""Web-service related subcommands for the cli."""
import asyncio
import typing

import rich_click as click

from kiara.utils import is_develop

if typing.TYPE_CHECKING:
    from kiara.api import KiaraAPI


@click.group()
@click.pass_context
def service(ctx):
    """(Web-)service-related sub-commands."""


@service.command()
@click.option(
    "--host", help="The host to bind to.", required=False, default="localhost:8080"
)
@click.pass_context
def start(ctx, host: str):
    """Start a kiara (web) service."""

    from kiara_plugin.service.openapi.service import KiaraOpenAPIService

    try:
        import uvloop

        uvloop.install()
    except Exception:
        pass

    kiara_api: KiaraAPI = ctx.obj.kiara_api
    kiara_service = KiaraOpenAPIService(kiara_api=kiara_api)
    from hypercorn.config import Config

    config = Config()
    config.bind = [host]

    if is_develop():
        config.use_reloader = True

    from hypercorn.asyncio import serve

    app = kiara_service.app()
    asyncio.run(serve(app, config))  # type: ignore
