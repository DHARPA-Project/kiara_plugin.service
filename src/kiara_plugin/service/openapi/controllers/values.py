# -*- coding: utf-8 -*-
import uuid
from typing import Any, Dict, List, Mapping, Union

from networkx import DiGraph
from networkx.readwrite import json_graph
from pydantic import BaseModel, Field
from starlite import (
    Controller,
)

from kiara.api import Kiara, KiaraAPI, Value, ValueSchema
from kiara.exceptions import InvalidValuesException
from kiara.interfaces.python_api import ValueInfo, ValuesInfo
from kiara.models.values.matchers import ValueMatcher
from kiara.models.values.value import SerializedData
from kiara_plugin.service.openapi.controllers import get, post


class InputsValidationData(BaseModel):

    inputs: Mapping[str, Any] = Field(description="The provided inputs.")
    inputs_schema: Mapping[str, ValueSchema] = Field(description="The inputs schemas.")


class ValueControllerJson(Controller):
    path = "/"

    @get(path="/ids", api_func=KiaraAPI.list_value_ids)
    async def list_value_ids(self, kiara_api: KiaraAPI) -> List[uuid.UUID]:

        result = kiara_api.list_value_ids()
        return result

    @get(path="/value_info/{value: str}", api_func=KiaraAPI.retrieve_value_info)
    async def get_value_info(self, kiara_api: KiaraAPI, value: str) -> ValueInfo:

        value_info = kiara_api.retrieve_value_info(value=value)
        return value_info

    # @post(path="/values", api_func=KiaraAPI.retrieve_values_info)
    # async def find_values(
    #     self, kiara_api: KiaraAPI, data: ValueMatcher
    # ) -> Dict[str, ValueInfo]:
    #
    #     matcher_data = data.dict()
    #
    #     result = kiara_api.retrieve_values_info(**matcher_data).item_infos
    #     return result  # type: ignore

    @post(path="/values_info", api_func=KiaraAPI.retrieve_values_info)
    async def get_values_info(
        self, kiara_api: KiaraAPI, data: ValueMatcher
    ) -> Dict[str, ValueInfo]:

        matcher_data = data.dict()

        result = kiara_api.retrieve_values_info(**matcher_data)
        return result.item_infos  # type: ignore

    @get(path="/type/{data_type:str}/values", api_func=KiaraAPI.list_values)
    async def find_values_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> Dict[str, Value]:

        matcher = ValueMatcher(data_types=[data_type])

        result = kiara_api.list_values(**matcher.dict())
        return result  # type: ignore
        # return {str(k): v for k, v in result.items()}

    @get(
        path="/type/{data_type:str}/values_info",
        summary="List values info of specific data type.",
    )
    async def find_values_info_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> ValuesInfo:

        matcher = ValueMatcher(data_types=[data_type])

        result = kiara_api.retrieve_values_info(**matcher.dict())
        return result

    @post(path="/alias_names", api_func=KiaraAPI.list_alias_names)
    async def list_alias_names(
        self, kiara_api: KiaraAPI, data: ValueMatcher
    ) -> List[str]:

        matcher_data = data.dict()
        result = kiara_api.list_alias_names(**matcher_data)
        return result

    @post(path="/aliases", api_func=KiaraAPI.list_aliases)
    async def list_aliases(
        self, kiara_api: KiaraAPI, data: ValueMatcher
    ) -> Dict[str, Value]:

        matcher_data = data.dict()

        result = kiara_api.list_aliases(**matcher_data)
        return result  # type: ignore

    @post(path="/aliases_info", api_func=KiaraAPI.retrieve_aliases_info)
    async def list_aliases_info(
        self, kiara_api: KiaraAPI, data: ValueMatcher
    ) -> Dict[str, ValueInfo]:

        if data is None:
            matcher_data = {}
        else:
            matcher_data = data.dict()

        result = kiara_api.retrieve_aliases_info(**matcher_data)
        return result.item_infos  # type: ignore

    @get(path="/type/{data_type:str}/aliases", api_func=KiaraAPI.list_aliases)
    async def find_value_aliases_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> Dict[str, Value]:

        matcher = ValueMatcher(data_types=[data_type], has_alias=True)

        result = kiara_api.list_aliases(**matcher.dict())
        return result  # type: ignore

    @get(path="/type/{data_type:str}/alias_names", api_func=KiaraAPI.list_alias_names)
    async def find_value_aliase_names_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> List[str]:
        matcher = ValueMatcher(data_types=[data_type], has_alias=True)

        result = kiara_api.list_alias_names(**matcher.dict())
        return result

    @get(
        path="/type/{data_type:str}/aliases_info",
        api_func=KiaraAPI.retrieve_aliases_info,
    )
    async def find_value_aliases_info_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> ValuesInfo:

        matcher = ValueMatcher(data_types=[data_type], has_alias=True)

        result = kiara_api.retrieve_aliases_info(**matcher.dict())
        return result

    @get(
        path="/serialized/{value:uuid}",
        summary="Retrieve the serialized form of the values data.",
    )
    async def retrieve_data(
        self, kiara_api: KiaraAPI, value: Union[str, uuid.UUID]
    ) -> SerializedData:

        _value = kiara_api.get_value(value)
        return _value.serialized_data

    async def filter_data(self, kiara: Kiara, value):
        raise NotImplementedError()

    @post(path="/validate/inputs", summary="Validate inputs against a schema.")
    async def validate_inputs(
        self, kiara_api: KiaraAPI, data: InputsValidationData
    ) -> Dict[str, str]:

        print("VALIDATE REQUEST")
        try:
            value_map = kiara_api.context.data_registry.create_valuemap(
                data=data.inputs, schema=data.inputs_schema
            )
            return value_map.check_invalid()
        except InvalidValuesException as ive:
            return dict(ive.invalid_inputs)

    @get(path="/lineage/{value:str}", summary="Retrieve the lineage data for a value.")
    async def get_value_lineage(
        self, kiara_api: KiaraAPI, value: str
    ) -> Dict[str, Any]:

        print(f"LINEAGE REQUEST: {value}")
        _value = kiara_api.get_value(value=value)
        try:
            graph: DiGraph = _value.lineage.module_graph
            result = json_graph.node_link_data(graph)
            return result
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise e


# class ValueControllerHtmx(Controller):
#     path = "/"
#
#     @get(path="/", media_type=MediaType.HTML)
#     async def get_root_page(self, kiara: Kiara) -> Template:
#
#         return Template(
#             name="kiara_plugin.service/values/index.html", context={"kiara": kiara}
#         )
#
#     # @get(path="/values/aliases", media_type=MediaType.HTML)
#     # def get_alias_select_box(self, kiara: Kiara) -> Template:
#     #     return Template(name="kiara_plugin.service/values/alias_select.html", context={"kiara": kiara})
#
#     @post(path="/select", media_type=MediaType.HTML)
#     async def get_value_select(
#         self,
#         kiara_api: KiaraAPI,
#         data: DataTypeRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
#     ) -> Template:
#
#         if data and data.data_type:
#             data_types = [data.data_type]
#         else:
#             data_types = []
#
#         print(f"DATA_SELECT: {data_types}")
#
#         if data and data.data_type:
#             data_types = [data.data_type]
#         else:
#             data_types = []
#
#         return Template(
#             name="kiara_plugin.service/values/value_select.html",
#             context={"data_types": data_types, "field_name": "__no_field_name__"},
#         )
#
#     @post(path="/render", media_type=MediaType.HTML)
#     async def render_value(
#         self,
#         kiara_api: KiaraAPI,
#         data: RenderRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
#     ) -> Template:
#
#         print(f"RENDER REQUEST: {data}")
#         try:
#
#             if not hasattr(data, data.field_name):
#                 raise Exception(
#                     f"Request is missing the value attribute '{data.field_name}'."
#                 )
#
#             value_id = getattr(data, data.field_name)
#
#             value = kiara_api.get_value(value=value_id)
#
#             print("-------")
#             print(value)
#             render_conf = data.render_conf
#             if render_conf is None:
#                 render_conf = {}
#
#             print(render_conf)
#
#             render_result = kiara_api.render_value(
#                 value=value,
#                 target_format=["html", "string"],
#                 render_config=render_conf,
#             )
#         except Exception as e:
#             import traceback
#
#             traceback.print_exc()
#             raise e
#
#         return Template(
#             name="kiara_plugin.service/values/value_view.html",
#             context={
#                 "element_id": data.target_id,
#                 "render_value_result": render_result,
#                 "value_id": str(value.value_id),
#                 "field_name": data.field_name,
#             },
#         )
#
#     @post(path="/input_widget", media_type=MediaType.HTML)
#     async def get_input_element_for_type(
#         self,
#         kiara_api: KiaraAPI,
#         template_registry: TemplateRegistry,
#         data: DataTypeModel = Body(media_type=RequestEncodingType.URL_ENCODED),
#     ) -> str:
#
#         print(f"INPUT FIELD REQUEST: {data.data_type}")
#
#         data_type_cls = kiara_api.context.type_registry.get_data_type_cls(
#             type_name=data.data_type
#         )
#         data_type_instance = data_type_cls(**data.type_config)
#
#         alias_map = kiara_api.list_aliases(data_types=[data.data_type])
#
#         try:
#             template = template_registry.get_template(
#                 f"kiara_plugin.service/values/inputs/{data.data_type}.html"
#             )
#             rendered = template.render(
#                 data_type_instance=data_type_instance,
#                 alias_map=alias_map,
#                 data_type_name=data.data_type,
#                 field_name=data.field_name,
#             )
#         except Exception as e:
#             rendered = str(e)
#
#         return rendered
