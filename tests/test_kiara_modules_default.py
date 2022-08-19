#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `kiara_plugin.service` package."""

import pytest  # noqa

import kiara_plugin.service


def test_assert():

    assert kiara_plugin.service.get_version() is not None
