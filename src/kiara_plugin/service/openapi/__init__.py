# -*- coding: utf-8 -*-
from typing import Any, Dict, Union

from pydantic import BaseModel, Extra, Field
from starlite import Controller, MediaType, get, post

from kiara.context import Kiara


class OperationControllerHtml(Controller):
    path = "/operation"

    @get(path="/{operation_name:str}", media_type=MediaType.HTML)
    def get_operation(self, operation_name: str, kiara: Kiara) -> str:

        op_info = kiara.context_info.operations.type_infos.get(operation_name)  # type: ignore
        return op_info.create_html()

    @post("/search_operation", media_type=MediaType.HTML)
    def search_operation(self, search_term: str, kiara: Kiara) -> str:

        for op in kiara.context_info.operations:
            pass

        return "xxx"


class DataTypeRequest(BaseModel):

    data_type: str = Field(description="The data type.", default="any")


class RenderRequest(BaseModel):
    class Config:
        extra = Extra.allow

    target_id: str = Field(description="The id of the target element.")
    field_name: str = Field(description="The field name.")
    render_conf: Union[Dict[str, Any], None] = Field(
        description="The scene render config.", default=None
    )


class DataTypeModel(BaseModel):

    field_name: str = Field(description="The field name.")
    data_type: str = Field(description="The data type.")
    type_config: Dict[str, str] = Field(
        description="The (optional) data type configuration.", default_factory=dict
    )
