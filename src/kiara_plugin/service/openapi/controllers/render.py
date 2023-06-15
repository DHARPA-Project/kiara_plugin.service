# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Mapping, Union

from pydantic import BaseModel, Field
from starlite import Controller

from kiara.api import KiaraAPI, ValueSchema
from kiara.models.module.operation import Operation
from kiara.models.rendering import RenderValueResult
from kiara_plugin.service.openapi.controllers import get, post


class InputsValidationData(BaseModel):

    inputs: Mapping[str, Any] = Field(description="The provided inputs.")
    inputs_schema: Mapping[str, ValueSchema] = Field(description="The inputs schemas.")


class RenderControllerJson(Controller):
    path = "/"

    @get(
        path="/create_render_manifest/{data_type:str}",
        api_func=KiaraAPI.assemble_render_pipeline,
    )
    async def create_render_manifest(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> Operation:
        """Create a render manifest for the specified data type."""

        filters = ["select_columns"]
        operation = kiara_api.assemble_render_pipeline(
            data_type=data_type, target_format="html", filters=filters
        )
        return operation

    @post(path="/value/{value:str}/{target_format:str}", api_func=KiaraAPI.render_value)
    async def render_data(
        self,
        kiara_api: KiaraAPI,
        value: str,
        target_format: str = "html",
        data: Union[None, Dict[str, Any]] = None,
    ) -> RenderValueResult:
        """Queue a render job for the specified value id or alias.

        Arguments:
            value: the value id or alias
            target_format: the render format
            data: (optional) target & data type specific render configuration

        Returns:
            the render result
        """

        # filters = ["select_columns", "drop_columns"]
        filters: List[str] = []
        v = kiara_api.get_value(value)
        result = kiara_api.render_value(
            value=v, target_format=target_format, filters=filters, render_config=data
        )
        return result

    @post(
        path="/value_info/{value:str}/{target_format:str}",
        summary="Render value info as HTML",
    )
    async def render_operation_info(
        self,
        kiara_api: KiaraAPI,
        value: str,
        target_format: str = "html",
        data: Union[Dict[str, Any], None] = None,
    ) -> str:

        print(f"RENDER VALUE INFO REQUEST: {value}")

        value_info = kiara_api.retrieve_value_info(value)
        html = value_info.create_html()
        return html
