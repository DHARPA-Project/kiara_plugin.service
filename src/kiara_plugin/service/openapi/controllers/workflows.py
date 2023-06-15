# -*- coding: utf-8 -*-
from typing import Dict, List, Union

from pydantic import BaseModel, Field
from starlite import Controller

from kiara.api import KiaraAPI
from kiara.models.workflow import WorkflowInfo
from kiara_plugin.service.openapi.controllers import get, post


class WorkflowMatcher(BaseModel):

    filters: List[str] = Field(
        description="The (optional) filter strings, an operation must match all of them to be included in the result.",
        default_factory=list,
    )


class WorkflowControllerJson(Controller):
    path = "/"

    @post(path="/ids", api_func=KiaraAPI.retrieve_workflows_info)
    async def list_workflows(
        self, kiara_api: KiaraAPI, data: Union[WorkflowMatcher, None] = None
    ) -> Dict[str, WorkflowInfo]:

        # if data is None:
        #     filters: List[str] = []
        # else:
        #     filters = data.filters

        result = kiara_api.retrieve_workflows_info().item_infos
        return result  # type: ignore

    @post(path="/aliases", api_func=KiaraAPI.list_workflow_alias_names)
    async def list_workflow_aliases(
        self, kiara_api: KiaraAPI, data: Union[WorkflowMatcher, None] = None
    ) -> List[str]:

        # if data is None:
        #     filters: List[str] = []
        # else:
        #     filters = data.filters

        result = kiara_api.list_workflow_alias_names()
        return result

    @get(
        path="/workflow_info/{workflow: str}", api_func=KiaraAPI.retrieve_workflow_info
    )
    async def get_workflow_info(
        self, kiara_api: KiaraAPI, workflow: str
    ) -> WorkflowInfo:

        print(f"INFO: {workflow}")
        workflow_info = kiara_api.retrieve_workflow_info(workflow=workflow)
        return workflow_info
