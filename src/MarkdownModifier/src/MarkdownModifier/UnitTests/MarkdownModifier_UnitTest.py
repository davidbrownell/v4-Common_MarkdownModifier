# ----------------------------------------------------------------------
# |
# |  MarkdownModifier_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-11 10:52:57
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Integration tests for MarkdownModifier.py"""

# Note that this isn't a true unit test (it is actually an integration test). However,
# it is labeled as a unit test so that code coverage numbers can be enforced during
# the build process.

import re
import sys
import textwrap

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock as Mock

import pytest

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx
from Common_Foundation import TextwrapEx
from Common_Foundation.Types import overridemethod


# ----------------------------------------------------------------------
sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent.parent.parent)))
with ExitStack(lambda: sys.path.pop(0)):
    from MarkdownModifier.MarkdownModifier import Modify
    from MarkdownModifier.Plugin import Plugin


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Plugin1(Plugin):
    # ----------------------------------------------------------------------
    name: ClassVar[str]                     = "Plugin1"

    raise_preprocess: bool                  = field(kw_only=True, default=False)
    raise_execute: bool                     = field(kw_only=True, default=False)
    raise_postprocess: bool                 = field(kw_only=True, default=False)
    raise_finalize: bool                    = field(kw_only=True, default=False)

    # ----------------------------------------------------------------------
    @overridemethod
    def Preprocess(
        self,
        filename: Path,
        content: str,
    ) -> str:
        if self.raise_preprocess:
            raise Exception("Preprocess exception")

        return textwrap.dedent(
            """\
            Preprocess ({})
            filename: {}
            content:
                ----
            {}
                ----
            """,
        ).format(
            self.name,
            filename,
            TextwrapEx.Indent(content, 4).rstrip(),
        )

    # ----------------------------------------------------------------------
    @overridemethod
    def Execute(
        self,
        filename: Path,
        *args,
        **kwargs,
    ) -> str:
        if self.raise_execute:
            raise Exception("Execute exception")

        return textwrap.dedent(
            """\
            Execute ({})
            filename: {}
            args: {}
            kwargs: {}
            """,
        ).format(self.name, filename, args, kwargs)

    # ----------------------------------------------------------------------
    @overridemethod
    def Postprocess(
        self,
        filename: Path,
        content: str,
    ) -> str:
        if self.raise_postprocess:
            raise Exception("Postprocess exception")

        return textwrap.dedent(
            """\
            Postprocess ({})
            filename: {}
            content:
                ----
            {}
                ----
            """,
        ).format(
            self.name,
            filename,
            TextwrapEx.Indent(content, 4, ).rstrip(),
        )

    # ----------------------------------------------------------------------
    @overridemethod
    def Finalize(
        self,
        filename: Path,
        content: str,
    ) -> None:
        if self.raise_finalize:
            raise Exception("Finalize exception")


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Plugin2(Plugin):
    # ----------------------------------------------------------------------
    name: ClassVar[str]                     = "Plugin2"

    # ----------------------------------------------------------------------
    @overridemethod
    def Execute(
        self,
        filename: Path,
        *args,
        **kwargs,
    ) -> str:
        return textwrap.dedent(
            """\
            Execute ({})
            filename: {}
            args: {}
            kwargs: {}
            """,
        ).format(self.name, filename, args, kwargs)


# ----------------------------------------------------------------------
def test_Standard(_content):
    on_update_mock = Mock()

    assert Modify(
        Path("the_filename"),
        _content,
        [Plugin1(), Plugin2()],
        on_update_mock,
    ) == textwrap.dedent(
        """\
        Postprocess (Plugin1)
        filename: the_filename
        content:
            ----
            Preprocess (Plugin1)
            filename: the_filename
            content:
                ----
                1a: begin
                <!-- [[[Plugin1(1, 2, 3)]]] -->
                Execute (Plugin1)
                filename: the_filename
                args: (1, 2, 3)
                kwargs: {}
                <!-- [[[end]]] -->
                1a: end

                2: begin
                <!-- [[[Plugin2('a', 'b', 'c')]]] -->
                Execute (Plugin2)
                filename: the_filename
                args: ('a', 'b', 'c')
                kwargs: {}
                <!-- [[[end]]] -->
                2: end

                2b: begin
                <!-- [[[Plugin1(a=10, b=20, c=30, d=40)]]] -->
                Execute (Plugin1)
                filename: the_filename
                args: ()
                kwargs: {'a': 10, 'b': 20, 'c': 30, 'd': 40}
                <!-- [[[end]]] -->
                2b: end
                ----
            ----
        """,
    )


# ----------------------------------------------------------------------
def test_Include(_content):
    assert Modify(
        Path("the filename"),
        _content,
        [Plugin1(), Plugin2()],
        Mock(),
        include_plugin_names=set(["Plugin2"]),
    ) == textwrap.dedent(
        """\
        1a: begin
        <!-- [[[Plugin1(1, 2, 3)]]] -->

        <!-- [[[end]]] -->
        1a: end

        2: begin
        <!-- [[[Plugin2('a', 'b', 'c')]]] -->
        Execute (Plugin2)
        filename: the filename
        args: ('a', 'b', 'c')
        kwargs: {}
        <!-- [[[end]]] -->
        2: end

        2b: begin
        <!-- [[[Plugin1(a=10, b=20, c=30, d=40)]]] -->

        <!-- [[[end]]] -->
        2b: end
        """,
    )


# ----------------------------------------------------------------------
def test_Exclude(_content):
    assert Modify(
        Path("***filename***"),
        _content,
        [Plugin1(), Plugin2()],
        Mock(),
        exclude_plugin_names=set(["Plugin1"]),
    ) == textwrap.dedent(
        """\
        1a: begin
        <!-- [[[Plugin1(1, 2, 3)]]] -->

        <!-- [[[end]]] -->
        1a: end

        2: begin
        <!-- [[[Plugin2('a', 'b', 'c')]]] -->
        Execute (Plugin2)
        filename: ***filename***
        args: ('a', 'b', 'c')
        kwargs: {}
        <!-- [[[end]]] -->
        2: end

        2b: begin
        <!-- [[[Plugin1(a=10, b=20, c=30, d=40)]]] -->

        <!-- [[[end]]] -->
        2b: end
        """,
    )


# ----------------------------------------------------------------------
class TestExceptions(object):
    # ----------------------------------------------------------------------
    def test_Preprocess(self):
        with pytest.raises(
            Exception,
            match=re.escape("Plugin1: Preprocess exception"),
        ):
            Modify(
                Path("filename"),
                textwrap.dedent(
                    """\
                    <!-- [[[Plugin1()]]] -->
                    <!-- [[[end]]] -->
                    """,
                ),
                [Plugin1(raise_preprocess=True)],
                Mock(),
            )

    # ----------------------------------------------------------------------
    def test_Execute(self):
        with pytest.raises(
            Exception,
            match=re.escape("Plugin1: Execute exception"),
        ):
            Modify(
                Path("filename"),
                textwrap.dedent(
                    """\
                    <!-- [[[Plugin1()]]] -->
                    <!-- [[[end]]] -->
                    """,
                ),
                [Plugin1(raise_execute=True)],
                Mock(),
            )

    # ----------------------------------------------------------------------
    def test_Postprocess(self):
        with pytest.raises(
            Exception,
            match=re.escape("Plugin1: Postprocess exception"),
        ):
            Modify(
                Path("filename"),
                textwrap.dedent(
                    """\
                    <!-- [[[Plugin1()]]] -->
                    <!-- [[[end]]] -->
                    """,
                ),
                [Plugin1(raise_postprocess=True)],
                Mock(),
            )

    # ----------------------------------------------------------------------
    def test_Finalize(self):
        with pytest.raises(
            Exception,
            match=re.escape("Plugin1: Finalize exception"),
        ):
            Modify(
                Path("filename"),
                textwrap.dedent(
                    """\
                    <!-- [[[Plugin1()]]] -->
                    <!-- [[[end]]] -->
                    """,
                ),
                [Plugin1(raise_finalize=True)],
                Mock(),
            )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def _content() -> str:
    return textwrap.dedent(
        """\
        1a: begin
        <!-- [[[Plugin1(1, 2, 3)]]] -->
        <!-- [[[end]]] -->
        1a: end

        2: begin
        <!-- [[[Plugin2('a', 'b', 'c')]]] -->
        <!-- [[[end]]] -->
        2: end

        2b: begin
        <!-- [[[Plugin1(a=10, b=20, c=30, d=40)]]] -->
        <!-- [[[end]]] -->
        2b: end
        """,
    )
