# -*- coding: utf-8 -*-
from typing import List

from kiara.context import Kiara
from kiara.interfaces.python_api import KiaraAPI
from kiara.interfaces.python_api.models.info import OperationInfo
from kiara.interfaces.python_api.models.job import JobDesc
from kiara.models.values.value import ValueMap
from starlite import Controller, get, post


class OperationControllerJson(Controller):
    path = "/operation"

    @get()
    async def list_operations(self, kiara_api: KiaraAPI) -> List[OperationInfo]:

        result = list(kiara.context_info.operations.item_infos.values())
        return result

    @get(path="/{operation_name:str}")
    def get_operation(self, operation_name: str, kiara: Kiara) -> OperationInfo:

        op_info = kiara.context_info.operations.item_infos.get(operation_name)
        return op_info


class JobControllerJson(Controller):

    path = "/"

    @post(path="/run")
    async def run_job(self, kiara_api: KiaraAPI, data: JobDesc) -> ValueMap:

        job_config = data.create_job_config(kiara=kiara)
        job_id = kiara.job_registry.execute_job(job_config=job_config, wait=True)
        result = kiara.job_registry.retrieve_result(job_id=job_id)

        return result
