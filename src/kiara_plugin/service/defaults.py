# -*- coding: utf-8 -*-
import os
import sys

from appdirs import AppDirs

kiara_html_app_dirs = AppDirs("kiara-service", "frkl")

if not hasattr(sys, "_MEIPASS"):
    KIARA_MODULE_BASE_FOLDER = os.path.dirname(__file__)
    """Marker to indicate the base folder for the `kiara_streamlit` module."""
else:
    KIARA_MODULE_BASE_FOLDER = os.path.join(sys._MEIPASS, "kiara")  # type: ignore
    """Marker to indicate the base folder for the `kiara_streamlit` module."""

KIARA_SERVICE_RESOURCES_FOLDER = os.path.join(KIARA_MODULE_BASE_FOLDER, "resources")
"""Default resources folder for this package."""
