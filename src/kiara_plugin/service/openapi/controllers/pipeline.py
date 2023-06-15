# -*- coding: utf-8 -*-
from typing import List

from pydantic import BaseModel, Field
from starlite import Controller

from kiara.api import KiaraAPI
from kiara.interfaces.python_api.models.info import PipelineStructureInfo
from kiara.utils.pipelines import get_pipeline_config
from kiara_plugin.service.openapi.controllers import get


class PipelineMatcher(BaseModel):

    filters: List[str] = Field(
        description="The (optional) filter strings, a pipeline must match all of them to be included in the result.",
        default_factory=list,
    )


class PipelineControllerJson(Controller):
    path = "/"

    @get(path="/structure/{pipeline:str}", api_func=get_pipeline_config)
    async def get_pipeline_structure(
        self, kiara_api: KiaraAPI, pipeline: str
    ) -> PipelineStructureInfo:

        print(f"PIPELINE: {pipeline}")
        pipeline_config = get_pipeline_config(pipeline=pipeline)
        info = PipelineStructureInfo.create_from_instance(
            kiara=kiara_api.context, instance=pipeline_config.structure
        )
        return info
