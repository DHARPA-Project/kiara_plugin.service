# -*- coding: utf-8 -*-

"""This module contains the metadata (and other) models that are used in the ``kiara_plugin.service`` package.

Those models are convenience wrappers that make it easier for *kiara* to find, create, manage and version metadata -- but also
other type of models -- that is attached to data, as well as *kiara* modules.

Metadata models must be a sub-class of [kiara.metadata.MetadataModel][kiara.metadata.MetadataModel]. Other models usually
sub-class a pydantic BaseModel or implement custom base classes.
"""
from typing import Any, Union

from pydantic import Field

from kiara.models import KiaraModel


class InternalErrorModel(KiaraModel):
    """A model describing an internal server-side error."""

    _kiara_model_id = "instance.internal_error"

    @classmethod
    def from_exception(cls, exception: Exception, status: Union[int, None] = None):

        if status is None:
            status = 500

        return InternalErrorModel.construct(
            status=status, msg=str(exception), exception=None
        )

    status: int = Field(description="The status code code.")
    msg: str = Field(description="The error message.")
    exception: Any = Field(
        description="More details about the underlying error.", default=None
    )
