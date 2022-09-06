# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional, TypeVar, Union, cast

import structlog
import yaml
from hypercorn.typing import ASGIFramework
from jinja2 import Template as JinjaTemplate
from jinja2 import TemplateNotFound as JinjaTemplateNotFound
from kiara.context import Kiara
from kiara.interfaces.python_api import KiaraAPI
from kiara.models import KiaraModel
from kiara.registries.templates import TemplateRegistry
from kiara.utils import is_debug, is_develop
from orjson import (
    OPT_INDENT_2,
    OPT_NON_STR_KEYS,
    OPT_OMIT_MICROSECONDS,
    OPT_SERIALIZE_NUMPY,
    dumps,
)
from pydantic import DirectoryPath
from pydantic_openapi_schema.v3_1_0.open_api import OpenAPI
from starlette.responses import JSONResponse
from starlette.status import HTTP_204_NO_CONTENT, HTTP_304_NOT_MODIFIED
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
from starlite.enums import MediaType, OpenAPIMediaType
from starlite.exceptions import ImproperlyConfiguredException, TemplateNotFound
from starlite.exceptions.utils import create_exception_response
from starlite.template import TemplateEngineProtocol

from kiara_plugin.service.defaults import KIARA_SERVICE_RESOURCES_FOLDER
from kiara_plugin.service.models import InternalErrorModel
from kiara_plugin.service.openapi import OperationControllerHtml
from kiara_plugin.service.openapi.controllers.jobs import JobControllerJson
from kiara_plugin.service.openapi.controllers.operations import (
    OperationControllerHtmx,
    OperationControllerJson,
)
from kiara_plugin.service.openapi.controllers.render import RenderControllerJson
from kiara_plugin.service.openapi.controllers.values import (
    ValueControllerHtmx,
    ValueControllerJson,
)

T = TypeVar("T")


logger = structlog.getLogger()


class KiaraModelResponse(Response):
    def serializer(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, KiaraModel):
            return value.dict()
        return super().serializer(value)

    def render(self, content: Any) -> bytes:
        """
        Handles the rendering of content T into a bytes string.
        Args:
            content: An arbitrary value of type T

        Returns:
            An encoded bytes string
        """
        try:
            if (
                content is None
                or content is NoReturn
                and (
                    self.status_code < 100
                    or self.status_code in {HTTP_204_NO_CONTENT, HTTP_304_NOT_MODIFIED}
                )
            ):
                return b""
            if self.media_type == MediaType.JSON:
                return dumps(
                    content,
                    default=self.serializer,
                    option=OPT_SERIALIZE_NUMPY
                    | OPT_OMIT_MICROSECONDS
                    | OPT_NON_STR_KEYS,
                )
            if isinstance(content, OpenAPI):
                content_dict = content.dict(by_alias=True, exclude_none=True)
                if self.media_type == OpenAPIMediaType.OPENAPI_YAML:
                    encoded = yaml.dump(content_dict, default_flow_style=False).encode(
                        "utf-8"
                    )
                    return cast("bytes", encoded)
                return dumps(
                    content_dict,
                    option=OPT_INDENT_2 | OPT_OMIT_MICROSECONDS | OPT_NON_STR_KEYS,
                )
            return super().render(content)
        except (AttributeError, ValueError, TypeError) as e:
            raise ImproperlyConfiguredException(
                "Unable to serialize response content"
            ) from e


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


def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        {"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers
    )


def custom_exception_handler(request: Request, exc: Exception):
    model = InternalErrorModel.from_exception(exc)
    return JSONResponse({"detail": model.dict()}, status_code=model.status)


class KiaraOpenAPIService:
    def __init__(self, kiara_api: KiaraAPI):

        self._kiara_api: KiaraAPI = kiara_api
        self._app: Optional[ASGIFramework] = None
        self._resources_base: Path = Path(KIARA_SERVICE_RESOURCES_FOLDER)

    def app(self) -> ASGIFramework:
        if self._app is not None:
            return self._app

        from starlite import Router

        value_router = Router(path="/data", route_handlers=[ValueControllerJson])
        operation_router = Router(
            path="/operations", route_handlers=[OperationControllerJson]
        )
        job_router = Router(path="/jobs", route_handlers=[JobControllerJson])
        render_router = Router(path="/render", route_handlers=[RenderControllerJson])

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
        route_handlers.append(operation_router)
        route_handlers.append(job_router)
        route_handlers.append(render_router)
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
        exception_handlers[HTTPException] = http_exception_handler
        exception_handlers[Exception] = custom_exception_handler
        # if is_debug() or is_develop():
        #     exception_handlers[HTTPException] = logging_exception_handler
        # exception_handlers[Exception] = http_exception_handler

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
            response_class=KiaraModelResponse,
        )
        return self._app  # type: ignore
