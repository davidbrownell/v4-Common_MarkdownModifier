# ----------------------------------------------------------------------
# |
# |  Dev_LocalEndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-12 09:07:17
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""EndToEnd tests invoked from a development environment."""

import re
import sys
import textwrap

from pathlib import Path
from typing import Any, Callable, Optional
from unittest.mock import MagicMock as Mock

import click
import pytest

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx

# code_coverage: include = ../__main__.py


# ----------------------------------------------------------------------
sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent.parent.parent)))
with ExitStack(lambda: sys.path.pop(0)):
    from EntryPoint.__main__ import Execute, Validate


# ----------------------------------------------------------------------
class TestStandard(object):
    # ----------------------------------------------------------------------
    def test_Standard(self, _file_system, _executor):
        _executor(Path())

        assert _file_system.HasChanged(Path("One.md"))
        assert _file_system.HasChanged(Path("NotAMarkdownFile.txt")) is False
        assert _file_system.HasChanged(Path("Two.md"))
        assert _file_system.HasChanged(Path("Three.md")) is False
        assert _file_system.HasChanged(Path("Dir1/A.md")) is False
        assert _file_system.HasChanged(Path("Dir1/B.md"))
        assert _file_system.HasChanged(Path("Dir2/Dir3/10.md"))
        assert _file_system.HasChanged(Path("Dir2/Dir3/20.md"))

        assert Path("One.md").open().read() == textwrap.dedent(
            """\
            <!-- [[[ TableOfContents() ]]] -->
            <div>1 <a href="#heading-1">Heading 1</a></div>
            <div>&nbsp;&nbsp;1.1 <a href="#heading-2">Heading 2</a></div>
            <div>&nbsp;&nbsp;&nbsp;&nbsp;1.1.1 <a href="#heading-3">Heading 3</a></div>
            <!-- [[[end]]] -->

            # Heading 1
            ## Heading 2
            ### Heading 3
            """,
        )

        assert Path("Two.md").open().read() == textwrap.dedent(
            """\
            <!-- [[[
                DefinitionList(
                    {
                        "foo": "The definition for foo.",
                        "Bar": "The definition for Bar.",
                    },
                )
            ]]] -->
            <p>
              <div><i><a id="foo">foo</a></i></div>
              <div>&nbsp;&nbsp;The definition for <a href="#foo" data-definition-list-link=1>foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>&nbsp;&nbsp;The definition for <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
            </p>
            <!-- [[[end]]] -->

            <a href="#foo" data-definition-list-link=1>foo</a>
            <a href="#bar" data-definition-list-link=1>Bar</a>
            """,
        )

        assert Path("Dir1/B.md").open().read() == textwrap.dedent(
            """\
            <!-- [[[TableOfContents()]]] -->
            <div>1 <a href="#heading-1">Heading 1</a></div>
            <!-- [[[end]]] -->

            # Heading 1
            """,
        )

        assert Path("Dir2/Dir3/10.md").open().read() == textwrap.dedent(
            """\
            <!-- [[[TableOfContents()]]] -->
            <div>1 <a href="#heading-1">Heading 1</a></div>
            <!-- [[[end]]] -->

            # Heading 1
            """,
        )

        assert Path("Dir2/Dir3/20.md").open().read() == textwrap.dedent(
            """\
            <!-- [[[TableOfContents()]]] -->
            <div>1 <a href="#heading-1">Heading 1</a></div>
            <!-- [[[end]]] -->

            # Heading 1
            """,
        )

    # ----------------------------------------------------------------------
    def test_IncludeFile(self, _file_system, _executor):
        _executor(
            Path(),
            include_filenames=[re.compile("One.md"), ],
        )

        assert _file_system.HasChanged(Path("One.md"))
        assert _file_system.HasChanged(Path("Two.md")) is False
        assert _file_system.HasChanged(Path("Three.md")) is False
        assert _file_system.HasChanged(Path("Dir1/A.md")) is False
        assert _file_system.HasChanged(Path("Dir1/B.md")) is False
        assert _file_system.HasChanged(Path("Dir2/Dir3/10.md")) is False
        assert _file_system.HasChanged(Path("Dir2/Dir3/20.md")) is False

    # ----------------------------------------------------------------------
    def test_ExcludeFile(self, _file_system, _executor):
        _executor(
            Path(),
            exclude_filenames=[re.compile("Two.md"), ],
        )

        assert _file_system.HasChanged(Path("One.md"))
        assert _file_system.HasChanged(Path("NotAMarkdownFile.txt")) is False
        assert _file_system.HasChanged(Path("Two.md")) is False
        assert _file_system.HasChanged(Path("Three.md")) is False
        assert _file_system.HasChanged(Path("Dir1/A.md")) is False
        assert _file_system.HasChanged(Path("Dir1/B.md"))
        assert _file_system.HasChanged(Path("Dir2/Dir3/10.md"))
        assert _file_system.HasChanged(Path("Dir2/Dir3/20.md"))

    # ----------------------------------------------------------------------
    def test_IncludePlugin(self, _file_system, _executor):
        _executor(
            Path(),
            include_plugins=["TableOfContents", ],
        )

        assert _file_system.HasChanged(Path("One.md"))
        assert _file_system.HasChanged(Path("NotAMarkdownFile.txt")) is False
        assert _file_system.HasChanged(Path("Two.md")) is False
        assert _file_system.HasChanged(Path("Three.md")) is False
        assert _file_system.HasChanged(Path("Dir1/A.md"))
        assert _file_system.HasChanged(Path("Dir1/B.md"))
        assert _file_system.HasChanged(Path("Dir2/Dir3/10.md"))
        assert _file_system.HasChanged(Path("Dir2/Dir3/20.md"))

    # ----------------------------------------------------------------------
    def test_ExcludePlugin(self, _file_system, _executor):
        _executor(
            Path(),
            exclude_plugins=["TableOfContents", ],
        )

        assert _file_system.HasChanged(Path("One.md")) is False
        assert _file_system.HasChanged(Path("NotAMarkdownFile.txt")) is False
        assert _file_system.HasChanged(Path("Two.md"))
        assert _file_system.HasChanged(Path("Three.md")) is False
        assert _file_system.HasChanged(Path("Dir1/A.md")) is False
        assert _file_system.HasChanged(Path("Dir1/B.md")) is False
        assert _file_system.HasChanged(Path("Dir2/Dir3/10.md")) is False
        assert _file_system.HasChanged(Path("Dir2/Dir3/20.md")) is False


# ----------------------------------------------------------------------
class TestValidate(object):
    # ----------------------------------------------------------------------
    def test_Changes(self, _file_system, _validator):
        assert _validator(Path()) == 1

    # ----------------------------------------------------------------------
    def test_NoChanges(self, _file_system, _validator):
        assert _validator(Path("Three.md")) == 0


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _FileSystem(object):
    # ----------------------------------------------------------------------
    def __init__(self, fs):
        self._hold_fs = fs
        self._content: dict[Path, Optional[str]] = {
            Path("One.md"): textwrap.dedent(
                """\
                <!-- [[[ TableOfContents() ]]] -->

                <!-- [[[end]]] -->

                # Heading 1
                ## Heading 2
                ### Heading 3
                """,
            ),
            Path("NotAMarkdownFile.txt"): textwrap.dedent(
                """\
                <!-- [[[ TableOfContents() ]]] -->

                <!-- [[[end]]] -->

                # Heading 1
                ## Heading 2
                ### Heading 3
                """,
            ),
            Path("Two.md"): textwrap.dedent(
                """\
                <!-- [[[
                    DefinitionList(
                        {
                            "foo": "The definition for foo.",
                            "Bar": "The definition for Bar.",
                        },
                    )
                ]]] -->

                <!-- [[[end]]] -->

                foo
                Bar
                """,
            ),
            Path("Three.md"): textwrap.dedent(
                """\
                Nothing to change.
                """,
            ),
            Path("EmptyDir"): None,
            Path("Dir1/A.md"): textwrap.dedent(
                """\
                No changes will be made to this file.

                <!-- [[[
                DefinitionList(
                    {
                        "foo": "The definition for foo.",
                        "Bar": "The definition for Bar.",
                    },
                )
                ]]] -->
                <p>
                  <div><i><a id="foo">foo</a></i></div>
                  <div>&nbsp;&nbsp;The definition for <a href="#foo" data-definition-list-link=1>foo</a>.</div>
                </p>
                <p>
                  <div><i><a id="bar">Bar</a></i></div>
                  <div>&nbsp;&nbsp;The definition for <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
                </p>
                <!-- [[[end]]] -->

                <a href="#foo" data-definition-list-link=1>foo</a>
                <a href="#bar" data-definition-list-link=1>Bar</a>
                """,
            ),
            Path("Dir1/B.md"): textwrap.dedent(
                """\
                <!-- [[[TableOfContents()]]] -->

                <!-- [[[end]]] -->

                # Heading 1
                """,
            ),
            Path("Dir2/Dir3/10.md"): textwrap.dedent(
                """\
                <!-- [[[TableOfContents()]]] -->

                <!-- [[[end]]] -->

                # Heading 1
                """,
            ),
            Path("Dir2/Dir3/20.md"): textwrap.dedent(
                """\
                <!-- [[[TableOfContents()]]] -->

                <!-- [[[end]]] -->

                # Heading 1
                """,
            ),
        }

        for path, content in self._content.items():
            if content is None:
                path.mkdir(parents=True, exist_ok=True)
                continue

            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w") as f:
                f.write(content)

    # ----------------------------------------------------------------------
    def HasChanged(
        self,
        filename: Path,
    ) -> bool:
        with filename.open() as f:
            content = f.read()

        return content != self._content[filename]


# ----------------------------------------------------------------------
@pytest.fixture
def _file_system(fs) -> _FileSystem:
    return _FileSystem(fs)


# ----------------------------------------------------------------------
@pytest.fixture
def _executor() -> Callable[[Any], int]:
    # ----------------------------------------------------------------------
    def Executor(*args, **kwargs) -> int:
        try:
            Execute(
                *args,
                **{
                    **{
                        "include_filenames": [],
                        "exclude_filenames": [],
                        "include_plugins": [],
                        "exclude_plugins": [],
                        "quiet": False,
                        "verbose": False,
                        "debug": False,
                    },
                    **kwargs,
                },
            )
        except click.exceptions.Exit as ex:
            return ex.exit_code

        assert False, "Unexpected"

    # ----------------------------------------------------------------------

    return Executor


# ----------------------------------------------------------------------
@pytest.fixture
def _validator() -> Callable[[Any], int]:
    # ----------------------------------------------------------------------
    def Validator(*args, **kwargs) -> int:
        try:
            Validate(
                *args,
                **{
                    **{
                        "include_filenames": [],
                        "exclude_filenames": [],
                        "include_plugins": [],
                        "exclude_plugins": [],
                        "quiet": False,
                        "verbose": False,
                        "debug": False,
                    },
                    **kwargs,
                },
            )
        except click.exceptions.Exit as ex:
            return ex.exit_code

        assert False, "Unexpected"

    # ----------------------------------------------------------------------

    return Validator
