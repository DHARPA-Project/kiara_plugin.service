# -*- coding: utf-8 -*-
import uuid
from typing import Dict, List, Union

import orjson

from kiara import Kiara, KiaraAPI
from kiara.interfaces.python_api import OperationInfo
from kiara.interfaces.python_api.models.info import PipelineStructureInfo
from kiara.models.module.jobs import JobStatus
from kiara.models.workflow import WorkflowInfo
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


class WorkflowMatcher(BaseModel):

    filters: List[str] = Field(
        description="The (optional) filter strings, an operation must match all of them to be included in the result.",
        default_factory=list,
    )

class WorkflowControllerJson(Controller):
    path = "/"

    @post(path="/ids")
    async def list_workflows(
        self, kiara_api: KiaraAPI, data: Union[WorkflowMatcher, None] = None
    ) -> Dict[str, WorkflowInfo]:

        if data is None:
            filters: List[str] = []
        else:
            filters = data.filters

        return {}

    @post(path="/aliases")
    async def list_workflows(
        self, kiara_api: KiaraAPI, data: Union[WorkflowMatcher, None] = None
    ) -> Dict[str, WorkflowInfo]:

        if data is None:
            filters: List[str] = []
        else:
            filters = data.filters

        return {}

    @get(path="/workflow_info/{workflow: str}")
    async def get_workflow_info(self, kiara_api: KiaraAPI, workflow: str) -> WorkflowInfo:

        print(f"INFO: {workflow}")
        workflow_info = kiara_api.get_workflow_info(workflow=workflow)
        return workflow_info



