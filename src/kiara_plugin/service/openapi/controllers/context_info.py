# -*- coding: utf-8 -*-
from typing import Dict, List, Union

from pydantic import BaseModel, Field
from starlite import (
    Controller,
)

from kiara.api import KiaraAPI
from kiara.interfaces.python_api import ModuleTypeInfo
from kiara.models.runtime_environment.python import (
    PythonRuntimeEnvironment,
)
from kiara.models.values.value import DataTypeInfo
from kiara.registries.environment import EnvironmentRegistry
from kiara_plugin.service.openapi.controllers import get, post


class DataTypeMatcher(BaseModel):

    filters: List[str] = Field(
        description="The (optional) filter strings, a module must match all of them to be included in the result.",
        default_factory=list,
    )
    python_package: Union[str, None] = Field(
        description="If specified, only modules that are contained in this Python package are returned.",
        default=None,
    )


class DataTypeControllerJson(Controller):
    path = "/"

    @post(path="/", api_func=KiaraAPI.retrieve_module_types_info)
    async def list_data_types(
        self, kiara_api: KiaraAPI, data: DataTypeMatcher
    ) -> Dict[str, DataTypeInfo]:

        filters = data.filters
        python_package = data.python_package

        data_types = kiara_api.retrieve_data_types_info(
            filter=filters, python_package=python_package
        )
        return data_types.item_infos  # type: ignore

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


class KiaraContextControllerJson(Controller):

    path = "/"

    @get(path="/installed_plugins")
    async def list_installed_plugins(self, kiara_api: KiaraAPI) -> Dict[str, str]:
        """List the kiara version as well as names and versions of all available kiara plugins."""

        registry = EnvironmentRegistry.instance()
        python_env: PythonRuntimeEnvironment = registry.environments["python"]  # type: ignore

        plugins = {}
        for pkg in python_env.packages:  # type: ignore
            if pkg.name != "kiara" and pkg.name.startswith("kiara"):
                plugins[pkg.name] = pkg.version

        result = {}
        for name in sorted(plugins.keys()):
            result[name] = plugins[name]

        return result
