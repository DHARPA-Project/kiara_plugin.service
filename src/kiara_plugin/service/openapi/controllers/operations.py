# -*- coding: utf-8 -*-
import uuid
from typing import Dict, List, Union

from kiara import Kiara, KiaraAPI
from kiara.interfaces.python_api import OperationInfo
from kiara.models.module.jobs import JobStatus
from kiara.registries.templates import TemplateRegistry
from pydantic import BaseModel, Extra, Field
from starlite import (
    Body,
    Controller,
    MediaType,
    RequestEncodingType,
    Template,
    get,
    post,
)


class OperationRequest(BaseModel):
    element_id: str = Field(description="The id of the element to be created.")
    operation_id: str = Field(description="The id of the operation.")


class OperationRunRequest(BaseModel):
    class Config:
        extra = Extra.allow

    element_id: str = Field(description="The id of the element to be created.")
    operation_id: str = Field(description="The id of the operation.")


class MonitorJobRequest(BaseModel):

    element_id: str = Field(description="The id of the result element.")
    job_id: str = Field(description="The id of the job to monitor.")


class OperationMatcher(BaseModel):

    filters: List[str] = Field(
        description="The (optional) filter strings, an operation must match all of them to be included in the result.",
        default_factory=list,
    )
    include_internal: bool = Field(
        description="Whether to include internal operations in the result.",
        default=False,
    )


class OperationControllerJson(Controller):
    path = "/"

    @post(path="/")
    async def list_operations(
        self, kiara_api: KiaraAPI, data: Union[OperationMatcher, None] = None
    ) -> Dict[str, OperationInfo]:

        if data is None:
            filters: List[str] = []
            include_internal = False
        else:
            filters = data.filters
            include_internal = data.include_internal

        operations = kiara_api.get_operations_info(
            *filters, include_internal=include_internal
        )
        return operations.item_infos  # type: ignore

    @post(path="/ids")
    async def list_operation_ids(
        self, kiara_api: KiaraAPI, data: Union[OperationMatcher, None] = None
    ) -> List[str]:
        if data is None:
            filters: List[str] = []
            include_internal = False
        else:
            filters = data.filters
            include_internal = data.include_internal

        operation_ids = kiara_api.get_operation_ids(
            *filters, include_internal=include_internal
        )
        return operation_ids

    @get(path="/{operation_id:str}")
    def get_operation_info(
        self, kiara_api: KiaraAPI, operation_id: str
    ) -> OperationInfo:

        op = kiara_api.get_operation_info(operation_id=operation_id)
        return op


class OperationControllerHtmx(Controller):
    path = "/"

    @get(path="/", media_type=MediaType.HTML)
    def get_root_page(self, kiara: Kiara) -> Template:

        print("OPERATION ROOT REQUEST")
        return Template(
            name="kiara_plugin.service/operations/index.html", context={"kiara": kiara}
        )

    @post(path="/operation_info", media_type=MediaType.HTML)
    def render_operation_info(
        self,
        kiara_api: KiaraAPI,
        data: OperationRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
    ) -> Template:

        print(f"Operation info request: {data}")

        op_info = kiara_api.get_operation_info(operation_id=data.operation_id)

        return Template(
            name="kiara_plugin.service/operations/operation_view.html",
            context={"element_id": data.element_id, "operation_info": op_info},
        )

    @post(path="/inputs_form", media_type=MediaType.HTML)
    def get_input_form(
        self,
        kiara_api: KiaraAPI,
        template_registry: TemplateRegistry,
        data: OperationRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
    ) -> Template:

        print(f"INPUTS FORM REQUEST: {data}")
        op = kiara_api.get_operation(data.operation_id)

        fields = {}
        for field_name, schema in op.inputs_schema.items():

            data_type_cls = kiara_api.context.type_registry.get_data_type_cls(
                type_name=schema.type
            )

            template_name = f"kiara_plugin.service/values/inputs/{schema.type}.html"
            if template_name not in template_registry.template_names:
                data_type_instance = data_type_cls(**schema.type_config)
                if data_type_instance.characteristics.is_scalar:
                    template_name = (
                        f"kiara_plugin.service/values/inputs/generic-scalar.html"
                    )
                else:
                    template_name = f"kiara_plugin.service/values/inputs/generic.html"
            try:
                template = template_registry.get_template(template_name)
                rendered = template.render(
                    field_name=field_name,
                    data_type=schema.type,
                    desc=schema.doc.description,
                    doc=schema.doc.doc,
                )
            except Exception as e:
                import traceback

                traceback.print_exc()
                rendered = str(e)

            fields[field_name] = rendered

        dbg(fields)
        return Template(
            name="kiara_plugin.service/values/value_inputs_form.html",
            context={"fields": fields},
        )

    @post(path="/queue_job", media_type=MediaType.HTML)
    def queue_job(
        self,
        kiara_api: KiaraAPI,
        data: OperationRunRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
    ) -> Template:

        print(f"RUN REQUEST: {data.dict()}")

        try:
            inputs = data.dict()
            operation_id = inputs.pop("operation_id")
            element_id = inputs.pop("element_id")

            # because html forms don't send values for unchecked boxes
            op = kiara_api.get_operation(operation_id)
            for field_name, schema in op.inputs_schema.items():
                if field_name not in inputs.keys():
                    if schema.type == "boolean":
                        inputs[field_name] = False

            job_id = kiara_api.queue_job(operation=operation_id, inputs=inputs)

            job = kiara_api.get_job(job_id=job_id)
            return Template(
                name="kiara_plugin.service/jobs/job_monitor.html",
                context={"job": job, "element_id": element_id},
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            return f"<div>Can't submit job: {e}"

    @post(path="/monitor_job", media_type=MediaType.HTML)
    def monitor_job(
        self,
        kiara_api: KiaraAPI,
        data: MonitorJobRequest = Body(media_type=RequestEncodingType.URL_ENCODED),
    ) -> Template:

        print(f"MONITOR REQUEST: {data.dict()}")

        job_id = uuid.UUID(data.job_id)
        job = kiara_api.get_job(job_id=job_id)

        dbg(job.dict())

        if job.finished is None:
            return Template(
                name="kiara_plugin.service/jobs/job_monitor.html",
                context={"job": job, "element_id": data.element_id},
            )
        else:
            if job.status == JobStatus.SUCCESS:
                results = kiara_api.retrieve_job_result(job_id)
                error = None
            else:
                results = {}
                error = job.error
            return Template(
                name="kiara_plugin.service/jobs/job_finished.html",
                context={
                    "job": job,
                    "element_id": data.element_id,
                    "results": results,
                    "error": error,
                },
            )
