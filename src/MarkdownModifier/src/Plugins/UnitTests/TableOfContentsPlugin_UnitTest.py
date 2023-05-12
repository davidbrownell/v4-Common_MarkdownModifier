# ----------------------------------------------------------------------
# |
# |  TableOfContentsPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-08 14:19:40
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit tests for TableOfContentsPlugin.py"""

import re
import sys
import textwrap

from pathlib import Path
from unittest.mock import MagicMock as Mock
from typing import Iterable

import pytest

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx


# ----------------------------------------------------------------------
sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent.parent.parent)))
with ExitStack(lambda: sys.path.pop(0)):
    from Plugins.TableOfContentsPlugin import Plugin as TableOfContentsPlugin


# ----------------------------------------------------------------------
class TestSingle(object):
    # ----------------------------------------------------------------------
    def test_StandardPrefix(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>1 <a href="#one">One</a></div>
                <div>  1.1 <a href="#one1">One.1</a></div>
                <div>    1.1.1 <a href="#one11">One.1.1</a></div>
                <div>      1.1.1.1 <a href="#one-1111">One 1.1.1.1</a></div>
                <div>  1.2 <a href="#one2">One.2</a></div>
                <div>2 <a href="#two">Two</a></div>
                <div>  2.1 Unknown</div>
                <div>    2.1.1 <a href="#two11">Two.1.1</a></div>
                <div>3 <a href="#three">Three</a></div>
                <div>4 <a href="#four">Four</a></div>
                ---

                {}
                """,
            ).format(_content),
            content_template=textwrap.dedent(
                """\
                {table_of_contents}
                ---

                {content}
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_StandardSuffix(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                {}

                ---
                <div>1 <a href="#one">One</a></div>
                <div>  1.1 <a href="#one1">One.1</a></div>
                <div>    1.1.1 <a href="#one11">One.1.1</a></div>
                <div>      1.1.1.1 <a href="#one-1111">One 1.1.1.1</a></div>
                <div>  1.2 <a href="#one2">One.2</a></div>
                <div>2 <a href="#two">Two</a></div>
                <div>  2.1 Unknown</div>
                <div>    2.1.1 <a href="#two11">Two.1.1</a></div>
                <div>3 <a href="#three">Three</a></div>
                <div>4 <a href="#four">Four</a></div>
                """,
            ).format(_content),
            content_template=textwrap.dedent(
                """\
                {content}

                ---
                {table_of_contents}
                """,
            ),
        )

    # ----------------------------------------------------------------------
    def test_CustomIndentation(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>1 <a href="#one">One</a></div>
                <div>        1.1 <a href="#one1">One.1</a></div>
                <div>                1.1.1 <a href="#one11">One.1.1</a></div>
                <div>                        1.1.1.1 <a href="#one-1111">One 1.1.1.1</a></div>
                <div>        1.2 <a href="#one2">One.2</a></div>
                <div>2 <a href="#two">Two</a></div>
                <div>        2.1 Unknown</div>
                <div>                2.1.1 <a href="#two11">Two.1.1</a></div>
                <div>3 <a href="#three">Three</a></div>
                <div>4 <a href="#four">Four</a></div>
                {}
                """,
            ).format(_content),
            indentation=8,
        )

    # ----------------------------------------------------------------------
    def test_HeadingMin(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>1.1 <a href="#one1">One.1</a></div>
                <div>  1.1.1 <a href="#one11">One.1.1</a></div>
                <div>    1.1.1.1 <a href="#one-1111">One 1.1.1.1</a></div>
                <div>1.2 <a href="#one2">One.2</a></div>
                <div>  2.1.1 <a href="#two11">Two.1.1</a></div>
                {}
                """,
            ).format(_content),
            heading_min=2,
        )

    # ----------------------------------------------------------------------
    def test_HeadingMax(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>1 <a href="#one">One</a></div>
                <div>  1.1 <a href="#one1">One.1</a></div>
                <div>  1.2 <a href="#one2">One.2</a></div>
                <div>2 <a href="#two">Two</a></div>
                <div>3 <a href="#three">Three</a></div>
                <div>4 <a href="#four">Four</a></div>
                {}
                """,
            ).format(_content),
            heading_max=2,
        )

    # ----------------------------------------------------------------------
    def test_HeadingMinAndMax(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>1.1 <a href="#one1">One.1</a></div>
                <div>  1.1.1 <a href="#one11">One.1.1</a></div>
                <div>1.2 <a href="#one2">One.2</a></div>
                <div>  2.1.1 <a href="#two11">Two.1.1</a></div>
                {}
                """,
            ).format(_content),
            heading_min=2,
            heading_max=3,
        )

    # ----------------------------------------------------------------------
    def test_SimpleStrategy(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>- <a href="#one">One</a></div>
                <div>  * <a href="#one1">One.1</a></div>
                <div>    . <a href="#one11">One.1.1</a></div>
                <div>  * <a href="#one2">One.2</a></div>
                <div>- <a href="#two">Two</a></div>
                <div>  * Unknown</div>
                <div>    . <a href="#two11">Two.1.1</a></div>
                <div>- <a href="#three">Three</a></div>
                <div>- <a href="#four">Four</a></div>
                {}
                """,
            ).format(_content),
            line_item_prefix_strategy=TableOfContentsPlugin.LineItemPrefixType.Simple,
            heading_max=3,
        )

    # ----------------------------------------------------------------------
    def test_ListStrategy(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>A <a href="#one">One</a></div>
                <div>  B <a href="#one1">One.1</a></div>
                <div>    C <a href="#one11">One.1.1</a></div>
                <div>      D <a href="#one-1111">One 1.1.1.1</a></div>
                <div>  B <a href="#one2">One.2</a></div>
                <div>A <a href="#two">Two</a></div>
                <div>  B Unknown</div>
                <div>    C <a href="#two11">Two.1.1</a></div>
                <div>A <a href="#three">Three</a></div>
                <div>A <a href="#four">Four</a></div>
                {}
                """,
            ).format(_content),
            line_item_prefix_strategy=["A", "B", "C", "D", "E", "F", "G", ],
        )

    # ----------------------------------------------------------------------
    def test_CustomStrategy(self, _content):
        func_counter = 0

        # ----------------------------------------------------------------------
        def CustomPrefixGenerator(
            headings: list[TableOfContentsPlugin.HeadingInfo],
        ) -> str:
            nonlocal func_counter
            func_counter += 1

            return str(func_counter)

        # ----------------------------------------------------------------------

        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>1 <a href="#one">One</a></div>
                <div>  2 <a href="#one1">One.1</a></div>
                <div>    3 <a href="#one11">One.1.1</a></div>
                <div>      4 <a href="#one-1111">One 1.1.1.1</a></div>
                <div>  5 <a href="#one2">One.2</a></div>
                <div>6 <a href="#two">Two</a></div>
                <div>  7 Unknown</div>
                <div>    8 <a href="#two11">Two.1.1</a></div>
                <div>9 <a href="#three">Three</a></div>
                <div>10 <a href="#four">Four</a></div>
                {}
                """,
            ).format(_content),
            line_item_prefix_strategy=CustomPrefixGenerator,
        )

    # ----------------------------------------------------------------------
    def test_UnknownHeadingName(self, _content):
        _Execute(
            _content,
            textwrap.dedent(
                """\
                <div>1 <a href="#one">One</a></div>
                <div>  1.1 <a href="#one1">One.1</a></div>
                <div>    1.1.1 <a href="#one11">One.1.1</a></div>
                <div>      1.1.1.1 <a href="#one-1111">One 1.1.1.1</a></div>
                <div>  1.2 <a href="#one2">One.2</a></div>
                <div>2 <a href="#two">Two</a></div>
                <div>  2.1 ***Custom Name***</div>
                <div>    2.1.1 <a href="#two11">Two.1.1</a></div>
                <div>3 <a href="#three">Three</a></div>
                <div>4 <a href="#four">Four</a></div>
                {}
                """,
            ).format(_content),
            unknown_heading_name="***Custom Name***",
        )

    # ----------------------------------------------------------------------
    def test_CustomGenerateFunc(self, _content):
        # ----------------------------------------------------------------------
        def Generate(
            filename: Path,
            line_items: Iterable[TableOfContentsPlugin.LineItemInfo],
        ) -> str:
            return textwrap.dedent(
                """\
                Filename: {}
                Line Items:
                {}
                ---
                """,
            ).format(
                filename,
                "\n".join(str(line_item) for line_item in line_items),
            )

        # ----------------------------------------------------------------------

        _Execute(
            _content,
            textwrap.dedent(
                """\
                Filename: filename
                Line Items:
                Plugin.LineItemInfo(prefix='1', text='One', anchor='one')
                Plugin.LineItemInfo(prefix='  1.1', text='One.1', anchor='one1')
                Plugin.LineItemInfo(prefix='    1.1.1', text='One.1.1', anchor='one11')
                Plugin.LineItemInfo(prefix='      1.1.1.1', text='One 1.1.1.1', anchor='one-1111')
                Plugin.LineItemInfo(prefix='  1.2', text='One.2', anchor='one2')
                Plugin.LineItemInfo(prefix='2', text='Two', anchor='two')
                Plugin.LineItemInfo(prefix='  2.1', text='Unknown', anchor=None)
                Plugin.LineItemInfo(prefix='    2.1.1', text='Two.1.1', anchor='two11')
                Plugin.LineItemInfo(prefix='3', text='Three', anchor='three')
                Plugin.LineItemInfo(prefix='4', text='Four', anchor='four')
                ---

                {}
                """,
            ).format(_content),
            generate_table_of_contents_func=Generate,
        )


# ----------------------------------------------------------------------
def test_MultipleSections(_content):
    plugin = TableOfContentsPlugin()
    filename = Path("filename")

    original_content = _content
    _content += "\n\n"

    _content += plugin.Execute(filename)
    _content += "\n\n"

    _content += plugin.Execute(filename, indentation=8)
    _content += "\n\n"

    _content += plugin.Execute(filename, heading_max=2)
    _content += "\n\n"

    assert plugin.Postprocess(filename, _content).replace("&nbsp;", " ") == textwrap.dedent(
        """\
        {}

        <div>1 <a href="#one">One</a></div>
        <div>  1.1 <a href="#one1">One.1</a></div>
        <div>    1.1.1 <a href="#one11">One.1.1</a></div>
        <div>      1.1.1.1 <a href="#one-1111">One 1.1.1.1</a></div>
        <div>  1.2 <a href="#one2">One.2</a></div>
        <div>2 <a href="#two">Two</a></div>
        <div>  2.1 Unknown</div>
        <div>    2.1.1 <a href="#two11">Two.1.1</a></div>
        <div>3 <a href="#three">Three</a></div>
        <div>4 <a href="#four">Four</a></div>

        <div>1 <a href="#one">One</a></div>
        <div>        1.1 <a href="#one1">One.1</a></div>
        <div>                1.1.1 <a href="#one11">One.1.1</a></div>
        <div>                        1.1.1.1 <a href="#one-1111">One 1.1.1.1</a></div>
        <div>        1.2 <a href="#one2">One.2</a></div>
        <div>2 <a href="#two">Two</a></div>
        <div>        2.1 Unknown</div>
        <div>                2.1.1 <a href="#two11">Two.1.1</a></div>
        <div>3 <a href="#three">Three</a></div>
        <div>4 <a href="#four">Four</a></div>

        <div>1 <a href="#one">One</a></div>
        <div>  1.1 <a href="#one1">One.1</a></div>
        <div>  1.2 <a href="#one2">One.2</a></div>
        <div>2 <a href="#two">Two</a></div>
        <div>3 <a href="#three">Three</a></div>
        <div>4 <a href="#four">Four</a></div>

        """,
    ).format(original_content)


# ----------------------------------------------------------------------
class TestErrors(object):
    # ----------------------------------------------------------------------
    def test_InvalidHeadingMin(self):
        with pytest.raises(
            ValueError,
            match=re.escape("heading values must be >= 1."),
        ):
            TableOfContentsPlugin().Execute(Path(""), heading_min=0)

    # ----------------------------------------------------------------------
    def test_InvalidHeadingMax(self):
        with pytest.raises(
            ValueError,
            match=re.escape("min heading values must be <= max heading values."),
        ):
            TableOfContentsPlugin().Execute(
                Path(""),
                heading_min=3,
                heading_max=2,
            )

    # ----------------------------------------------------------------------
    def test_InvalidIndentation(self):
        with pytest.raises(
            ValueError,
            match=re.escape("indentation values must be >= 0."),
        ):
            TableOfContentsPlugin().Execute(
                Path(""),
                indentation=-1,
            )

    # ----------------------------------------------------------------------
    def test_InvalidNumValues(self):
        with pytest.raises(
            ValueError,
            match=re.escape("6 line item prefix values were expected but 3 were provided."),
        ):
            TableOfContentsPlugin().Execute(
                Path(""),
                line_item_prefix_strategy=["1", "2", "3", ],
            )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Execute(
    content: str,
    expected: str,
    *,
    content_template: str=textwrap.dedent(
        """\
        {table_of_contents}
        {content}
        """,
    ),
    **kwargs,
) -> None:
    plugin = TableOfContentsPlugin()
    filename = Path("filename")

    assert plugin.Postprocess(
        filename,
        content_template.format(
            table_of_contents=plugin.Execute(filename, **kwargs),
            content=content,
        ),
    ).replace("&nbsp;", " ") == expected


# ----------------------------------------------------------------------
@pytest.fixture
def _content() -> str:
    return textwrap.dedent(
        """\
        # One
        ## One.1
        ### One.1.1
        #### One 1.1.1.1
        ## One.2
        # Two
        ### Two.1.1
        # Three
        # Four
        """,
    )
