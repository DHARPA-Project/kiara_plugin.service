# -*- coding: utf-8 -*-
import uuid
from typing import Any, Dict, List, Mapping, Union

from kiara import Kiara, KiaraAPI, Value, ValueSchema
from kiara.exceptions import InvalidValuesException
from kiara.interfaces.python_api import ValueInfo, ValuesInfo
from kiara.models.module.operation import Operation
from kiara.models.values.matchers import ValueMatcher
from kiara.models.values.value import SerializedData
from kiara.registries.templates import TemplateRegistry
from pydantic import BaseModel, Field
from starlite import (
    Body,
    Controller,
    MediaType,
    RequestEncodingType,
    Template,
    get,
    post,
)

from kiara_plugin.service.openapi import DataTypeModel, DataTypeRequest, RenderRequest


class InputsValidationData(BaseModel):

    inputs: Mapping[str, Any] = Field(description="The provided inputs.")
    inputs_schema: Mapping[str, ValueSchema] = Field(description="The inputs schemas.")


class ValueControllerJson(Controller):
    path = "/"

    @get(path="/ids")
    async def list_valueids(self, kiara_api: KiaraAPI) -> List[uuid.UUID]:

        result = kiara_api.get_value_ids()
        return result

    @post(path="/values")
    async def find_values(
        self, kiara_api: KiaraAPI, data: Union[None, ValueMatcher] = None
    ) -> Dict[str, ValueInfo]:

        if data is None:
            matcher_data = {}
        else:
            matcher_data = data.dict()

        result = kiara_api.list_values(**matcher_data)
        return {str(k): v for k, v in result.items()}

    @post(path="/values_info")
    async def get_values_info(
        self, kiara_api: KiaraAPI, data: Union[None, ValueMatcher]
    ) -> Dict[str, ValueInfo]:

        if data is None:
            matcher_data = {}
        else:
            matcher_data = data.dict()

        result = kiara_api.get_values_info(**matcher_data)
        return result.item_infos

    @get(path="/type/{data_type:str}/values")
    async def find_values_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> Dict[str, Value]:

        matcher = ValueMatcher(data_types=[data_type])

        result = kiara_api.list_values(**matcher.dict())
        return {str(k): v for k, v in result.items()}

    @get(path="/type/{data_type:str}/values_info")
    async def find_values_info_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> ValuesInfo:

        matcher = ValueMatcher(data_types=[data_type])

        result = kiara_api.get_values_info(**matcher.dict())
        return result

    @post(path="/alias_names")
    async def list_alias_names(
        self, kiara_api: KiaraAPI, data: Union[ValueMatcher, None] = None
    ) -> List[str]:

        if data is None:
            matcher_data = {}
        else:
            matcher_data = data.dict()
        result = kiara_api.get_alias_names(**matcher_data)
        return result

    @post(path="/aliases")
    async def list_aliases(
        self, kiara_api: KiaraAPI, data: Union[ValueMatcher, None] = None
    ) -> Dict[str, Value]:

        if data is None:
            matcher_data = {}
        else:
            matcher_data = data.dict()

        result = kiara_api.list_aliases(**matcher_data)
        return result

    @post(path="/aliases_info")
    async def list_aliases_info(
        self, kiara_api: KiaraAPI, data: Union[ValueMatcher, None] = None
    ) -> Dict[str, ValueInfo]:

        if data is None:
            matcher_data = {}
        else:
            matcher_data = data.dict()

        result = kiara_api.get_aliases_info(**matcher_data)
        return result.item_infos

    @get(path="/type/{data_type:str}/aliases")
    async def find_value_aliases_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> Dict[str, Value]:

        matcher = ValueMatcher(data_types=[data_type], has_alias=True)

        result = kiara_api.list_aliases(**matcher.dict())
        return result

    @get(path="/type/{data_type:str}/alias_names")
    async def find_value_aliase_names_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> Dict[str, Value]:

        matcher = ValueMatcher(data_types=[data_type], has_alias=True)

        result = kiara_api.get_alias_names(**matcher.dict())
        return result

    @get(path="/type/{data_type:str}/aliases_info")
    async def find_value_aliases_info_of_type(
        self, kiara_api: KiaraAPI, data_type: str
    ) -> ValuesInfo:

        matcher = ValueMatcher(data_types=[data_type], has_alias=True)

        result = kiara_api.get_aliases_info(**matcher.dict())
        return result

    @get(path="/serialized/{value:uuid}")
    async def retrieve_data(
        self, kiara_api: KiaraAPI, value: Union[str, uuid.UUID]
    ) -> SerializedData:

        value = kiara_api.get_value(value)
        return value.serialized_data

    @post(path="/render/manifest/{data_type:str}")
    async def create_render_manifest(
        self, kiara_api: KiaraAPI, data_type: str, data: Union[Dict[str, Any]] = None
    ) -> Operation:

        filters = ["select_columns"]
        operation = kiara_api.assemble_render_pipeline(
            data_type=data_type, target_format="html", filters=filters
        )
        return operation

    @post(path="/render/{value:str}")
    async def render_data(
        self, kiara_api: KiaraAPI, value: str, data: Union[Dict[str, Any]] = None
    ) -> Operation:

        # filters = ["select_columns", "drop_columns"]
        filters = []
        v = kiara_api.get_value(value)
        operation = kiara_api.render_value(
            value=v, target_format="html", filters=filters, render_config=data
        )
        return operation

    async def filter_data(self, kiara: Kiara, value):
        raise NotImplementedError()

    @post(path="/validate/inputs")
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
            return ive.invalid_inputs


class ValueControllerHtmx(Controller):
    path = "/"

    @get(path="/", media_type=MediaType.HTML)
    def get_root_page(self, kiara: Kiara) -> Template:

        return Template(
            name="kiara_plugin.service/values/index.html", context={"kiara": kiara}
        )

    # @get(path="/values/aliases", media_type=MediaType.HTML)
    # def get_alias_select_box(self, kiara: Kiara) -> Template:
    #     return Template(name="kiara_plugin.service/values/alias_select.html", context={"kiara": kiara})

    @post(path="/select", media_type=MediaType.HTML)
    def get_value_select(
        self,
        kiara_api: KiaraAPI,
        data: DataTypeRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
    ) -> Template:

        if data and data.data_type:
            data_types = [data.data_type]
        else:
            data_types = []

        print(f"DATA_SELECT: {data_types}")

        if data and data.data_type:
            data_types = [data.data_type]
        else:
            data_types = []

        return Template(
            name="kiara_plugin.service/values/value_select.html",
            context={"data_types": data_types, "field_name": "__no_field_name__"},
        )

    @post(path="/render", media_type=MediaType.HTML)
    def render_value(
        self,
        kiara_api: KiaraAPI,
        data: RenderRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
    ) -> Template:

        print(f"RENDER REQUEST: {data}")

        if not hasattr(data, data.field_name):
            raise Exception(
                f"Request is missing the value attribute '{data.field_name}'."
            )

        value_id = getattr(data, data.field_name)

        value = kiara_api.get_value(value=value_id)

        render_result = kiara_api.render_value(
            value=value,
            target_format=["html", "string"],
            render_config=data.render_conf,
        )

        return Template(
            name="kiara_plugin.service/values/value_view.html",
            context={
                "element_id": data.target_id,
                "render_value_result": render_result,
                "value_id": str(value.value_id),
                "field_name": data.field_name,
            },
        )

    @post(path="/input_widget", media_type=MediaType.HTML)
    def get_input_element_for_type(
        self,
        kiara_api: KiaraAPI,
        template_registry: TemplateRegistry,
        data: DataTypeModel = Body(media_type=RequestEncodingType.URL_ENCODED),
    ) -> str:

        print(f"INPUT FIELD REQUEST: {data.data_type}")

        data_type_cls = kiara_api.context.type_registry.get_data_type_cls(
            type_name=data.data_type
        )
        data_type_instance = data_type_cls(**data.type_config)

        alias_map = kiara_api.list_aliases(data_types=[data.data_type])

        try:
            template = template_registry.get_template(
                f"kiara_plugin.service/values/inputs/{data.data_type}.html"
            )
            rendered = template.render(
                data_type_instance=data_type_instance,
                alias_map=alias_map,
                data_type_name=data.data_type,
                field_name=data.field_name,
            )
        except Exception as e:
            rendered = str(e)

        return rendered
