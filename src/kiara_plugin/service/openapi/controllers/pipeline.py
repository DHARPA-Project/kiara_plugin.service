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

from kiara.utils.pipelines import get_pipeline_config


class PipelineMatcher(BaseModel):

    filters: List[str] = Field(
        description="The (optional) filter strings, a pipeline must match all of them to be included in the result.",
        default_factory=list,
    )

class PipelineControllerJson(Controller):
    path = "/"

    @get(path="/structure/{pipeline:str}")
    async def get_pipeline_structure(self, kiara_api: KiaraAPI, pipeline: str) -> PipelineStructureInfo:

        print(f"PIPELINE: {pipeline}")
        pipeline_config = get_pipeline_config(pipeline=pipeline)
        info = PipelineStructureInfo.create_from_instance(kiara=kiara_api.context, instance=pipeline_config.structure)
        dbg(info.dict())
        return info


