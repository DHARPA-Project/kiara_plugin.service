# -*- coding: utf-8 -*-
from typing import Callable, Tuple, Union

import docstring_parser
from docstring_parser import DocstringStyle
from starlite import get as starlite_get
from starlite import post as starlite_post


def extract_doc(func: Callable) -> Tuple[Union[str, None], Union[str, None]]:

    doc = func.__doc__
    if not doc:
        return None, None

    docstring = docstring_parser.parse(doc, DocstringStyle.GOOGLE)
    summary = docstring.short_description
    description = docstring.long_description
    return summary, description


def get(*args, **kwargs) -> Callable:
    api_func = kwargs.pop("api_func", None)
    if api_func:
        summary, description = extract_doc(api_func)
        if summary:
            kwargs["summary"] = summary
        if description:
            kwargs["description"] = description
    return starlite_get(*args, **kwargs)


def post(*args, **kwargs) -> Callable:
    api_func = kwargs.pop("api_func", None)
    if api_func:
        kwargs["summary"], kwargs["description"] = extract_doc(api_func)
    return starlite_post(*args, **kwargs)
