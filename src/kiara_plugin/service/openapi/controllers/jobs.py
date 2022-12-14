# -*- coding: utf-8 -*-
from typing import Any, Mapping

from kiara import KiaraAPI
from kiara.models.module.jobs import ActiveJob
from pydantic import BaseModel, Extra, Field
from starlite import Controller, get, post


class RunJobRequest(BaseModel):
    class Config:
        extra = Extra.allow

    operation_id: str = Field(description="The id of the operation or module.")
    operation_config: Mapping[str, Any] = Field(
        description="The configuration of the operation.", default_factory=dict
    )
    inputs: Mapping[str, Any] = Field(description="The job input values.")


class JobInfoRequest(BaseModel):

    job_id: str = Field(description="The id of the job to monitor.")


class JobControllerJson(Controller):
    path = "/"

    @post(path="/queue_job")
    def queue_job(self, kiara_api: KiaraAPI, data: RunJobRequest) -> ActiveJob:

        print(f"JOB RUN REQUEST: {data.dict()}")

        try:
            operation_id = data.operation_id
            if not data.operation_config:
                job_id = kiara_api.queue_job(operation=operation_id, inputs=data.inputs)
            else:
                manifest = kiara_api.context.create_manifest(
                    module_or_operation=operation_id, config=data.operation_config
                )
                job_id = kiara_api.queue_job(operation=manifest, inputs=data.inputs)

            job = kiara_api.get_job(job_id=job_id)
            return job

        except Exception as e:
            import traceback

            traceback.print_exc()
            raise e

    @get(path="/monitor_job/{job_id:str}")
    def monitor_job(self, kiara_api: KiaraAPI, job_id: str) -> ActiveJob:

        print(f"MONITOR REQUEST: {job_id}")

        job = kiara_api.get_job(job_id=job_id)

        dbg(job.dict())

        return job
