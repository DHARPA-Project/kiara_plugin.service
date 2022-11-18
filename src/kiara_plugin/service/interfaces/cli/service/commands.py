# -*- coding: utf-8 -*-

#  Copyright (c) 2021, University of Luxembourg / DHARPA project
#  Copyright (c) 2021, Markus Binsteiner
#
#  Mozilla Public License, version 2.0 (see LICENSE or https://www.mozilla.org/en-US/MPL/2.0/)

"""Web-service related subcommands for the cli."""
import asyncio

import rich_click as click
from hypercorn.asyncio import serve
from kiara.interfaces.python_api import KiaraAPI
from kiara.utils import is_develop

from kiara_plugin.service.openapi.service import KiaraOpenAPIService


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
    import uvloop

    uvloop.install()

    kiara_api: KiaraAPI = ctx.obj["kiara_api"]
    kiara_service = KiaraOpenAPIService(kiara_api=kiara_api)
    from hypercorn.config import Config

    config = Config()
    config.bind = [host]

    if is_develop():
        config.use_reloader = True

    asyncio.run(serve(kiara_service.app(), config))
