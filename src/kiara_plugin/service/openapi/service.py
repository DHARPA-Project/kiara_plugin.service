# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List, Optional, Union, cast

import structlog
from hypercorn.typing import ASGIFramework
from jinja2 import Template as JinjaTemplate
from jinja2 import TemplateNotFound as JinjaTemplateNotFound
from kiara.context import Kiara
from kiara.interfaces.python_api import KiaraAPI
from kiara.registries.templates import TemplateRegistry
from kiara.utils import is_debug, is_develop
from pydantic import DirectoryPath
from starlite import (
    CORSConfig,
    HTTPException,
    Provide,
    Request,
    Response,
    Starlite,
    State,
    StaticFilesConfig,
    TemplateConfig,
)
from starlite.exceptions import TemplateNotFound
from starlite.exceptions.utils import create_exception_response
from starlite.template.base import TemplateEngineProtocol

from kiara_plugin.service.defaults import KIARA_SERVICE_RESOURCES_FOLDER
from kiara_plugin.service.openapi import OperationControllerHtml
from kiara_plugin.service.openapi.controllers import (
    JobControllerJson,
    OperationControllerJson,
)
from kiara_plugin.service.openapi.controllers.operations import OperationControllerHtmx
from kiara_plugin.service.openapi.controllers.values import (
    ValueControllerHtmx,
    ValueControllerJson,
)

logger = structlog.getLogger()


def logging_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Logs exception and returns appropriate response.

    Parameters
    ----------
    request : Request
        The request that caused the exception.
    exc :
        The exception caught by the Starlite exception handling middleware and passed to the
        callback.

    Returns
    -------
    Response
    """
    logger.error("Application Exception")
    return create_exception_response(exc)


class KiaraOpenAPIService:
    def __init__(self, kiara_api: KiaraAPI):

        self._kiara_api: KiaraAPI = kiara_api
        self._app: Optional[ASGIFramework] = None
        self._resources_base: Path = Path(KIARA_SERVICE_RESOURCES_FOLDER)

    def app(self) -> ASGIFramework:
        if self._app is not None:
            return self._app

        from starlite import Router

        job_router = Router(path="/job", route_handlers=[JobControllerJson])
        value_router = Router(
            path="/data", route_handlers=[OperationControllerJson, ValueControllerJson]
        )
        info_router_html = Router(
            path="/html/info", route_handlers=[OperationControllerHtml]
        )
        value_router_htmx = Router(
            path="/html/values", route_handlers=[ValueControllerHtmx]
        )
        operation_router_htmx = Router(
            path="/html/operations", route_handlers=[OperationControllerHtmx]
        )

        route_handlers = []
        route_handlers.append(value_router)
        route_handlers.append(value_router_htmx)
        route_handlers.append(operation_router_htmx)

        static_dir = self._resources_base / "static"

        static_file_config = [
            StaticFilesConfig(directories=[static_dir], path="/static")
        ]
        self._template_registry: TemplateRegistry = TemplateRegistry()

        environment = self._template_registry.environment

        class KiaraTemplateEngine(TemplateEngineProtocol[JinjaTemplate]):
            """Template engine using the default kiara template registry."""

            def __init__(
                self, directory: Union[DirectoryPath, List[DirectoryPath]]
            ) -> None:
                super().__init__(directory=directory)
                self.engine = environment

            def get_template(self, name: str) -> JinjaTemplate:
                """Loads the template with the name and returns it."""
                try:
                    return self.engine.get_template(name=name)
                except JinjaTemplateNotFound as exc:
                    raise TemplateNotFound(template_name=name) from exc

        def engine_callback(jinja_engine: KiaraTemplateEngine) -> KiaraTemplateEngine:
            jinja_engine.engine.globals["kiara_api"] = self._kiara_api
            return jinja_engine

        template_config = TemplateConfig(
            directory=[], engine=KiaraTemplateEngine, engine_callback=engine_callback
        )

        debug = is_debug() or is_develop()

        cors_config = CORSConfig()
        exception_handlers = {}

        if is_debug() or is_develop():
            exception_handlers[HTTPException] = logging_exception_handler

        def get_kiara_context(state: State) -> Kiara:
            if not hasattr(state, "kiara"):
                state.kiara = self._kiara_api.context
            return cast(Kiara, state.kiara)

        def get_kiara_api(state: State) -> KiaraAPI:
            if not hasattr(state, "kiara_api"):
                state.kiara_api = self._kiara_api
            return cast(KiaraAPI, state.kiara_api)

        def get_template_registry(state: State) -> TemplateRegistry:
            if not hasattr(state, "template_registry"):
                state.template_registry = self._template_registry
            return cast(TemplateRegistry, self._template_registry)

        dependencies = {
            "kiara": Provide(get_kiara_context),
            "kiara_api": Provide(get_kiara_api),
            "template_registry": Provide(get_template_registry),
        }

        self._app = Starlite(
            route_handlers=route_handlers,
            dependencies=dependencies,
            static_files_config=static_file_config,
            template_config=template_config,
            debug=debug,
            cors_config=cors_config,
            exception_handlers=exception_handlers,
        )
        return self._app  # type: ignore
