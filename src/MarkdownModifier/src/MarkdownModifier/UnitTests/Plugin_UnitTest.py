# ----------------------------------------------------------------------
# |
# |  Plugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-11 10:52:16
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit tests for Plugin.py."""

import re
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock as Mock

import pytest

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx
from Common_Foundation.Types import overridemethod


# ----------------------------------------------------------------------
sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent.parent.parent)))
with ExitStack(lambda: sys.path.pop(0)):
    from MarkdownModifier.Plugin import Plugin


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class MyPlugin(Plugin):
    name: ClassVar[str]                     = "MyPlugin"

    # ----------------------------------------------------------------------
    @overridemethod
    def Execute(
        self,
        filename: Path,
    ) -> str:
        return "executed"

# ----------------------------------------------------------------------
class TestCreateAnchorName(object):
    # ----------------------------------------------------------------------
    def test_Simple(self):
        assert Plugin.CreateAnchorName("Foo") == "foo"

    # ----------------------------------------------------------------------
    def test_WithSpaces(self):
        assert Plugin.CreateAnchorName("Foo Bar") == "foo-bar"

    # ----------------------------------------------------------------------
    def test_WithDots(self):
        assert Plugin.CreateAnchorName("Foo.Bar") == "foobar"


# ----------------------------------------------------------------------
class TestCreatePlaceholderId(object):
    # ----------------------------------------------------------------------
    def test_Standard(self):
        assert len(Plugin.CreatePlaceholderId()) == 64
        assert Plugin.CreatePlaceholderId() != Plugin.CreatePlaceholderId()


# ----------------------------------------------------------------------
def test_DefaultMethods():
    p = MyPlugin()

    assert p.Preprocess(Path("filename"), "foo") == "foo"
    assert p.Postprocess(Path("filename"), "foo") == "foo"
    p.Finalize(Path("filename"), "foo")


# ----------------------------------------------------------------------
def test_Execute():
    p = MyPlugin()

    assert p.Execute(Path("filename")) == "executed"
