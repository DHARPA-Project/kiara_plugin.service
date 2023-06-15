# -*- coding: utf-8 -*-
from typing import Dict, List, Union

from pydantic import BaseModel, Field
from starlite import (
    Controller,
)

from kiara.api import KiaraAPI
from kiara.interfaces.python_api import ModuleTypeInfo
from kiara_plugin.service.openapi.controllers import get, post

# class OperationRequest(BaseModel):
#     element_id: str = Field(description="The id of the element to be created.")
#     operation_id: str = Field(description="The id of the operation.")


class ModuleMatcher(BaseModel):

    filters: List[str] = Field(
        description="The (optional) filter strings, a module must match all of them to be included in the result.",
        default_factory=list,
    )
    python_package: Union[str, None] = Field(
        description="If specified, only modules that are contained in this Python package are returned.",
        default=None,
    )


class ModuleControllerJson(Controller):
    path = "/"

    @post(path="/", api_func=KiaraAPI.retrieve_module_types_info)
    async def list_module_types(
        self, kiara_api: KiaraAPI, data: ModuleMatcher
    ) -> Dict[str, ModuleTypeInfo]:

        filters = data.filters
        python_package = data.python_package

        module_types = kiara_api.retrieve_module_types_info(
            *filters, python_package=python_package
        )
        return module_types.item_infos  # type: ignore

    @get(path="/type_names", api_func=KiaraAPI.list_module_type_names)
    async def list_module_type_names(self, kiara_api: KiaraAPI) -> List[str]:
        """List the ids of all available operations."""

        module_names = kiara_api.list_module_type_names()
        return module_names

    @get(path="/{module_type_name:str}", api_func=KiaraAPI.retrieve_module_type_info)
    async def get_module_type_info(
        self, kiara_api: KiaraAPI, module_type_name: str
    ) -> ModuleTypeInfo:

        module = kiara_api.retrieve_module_type_info(module_type=module_type_name)
        return module
