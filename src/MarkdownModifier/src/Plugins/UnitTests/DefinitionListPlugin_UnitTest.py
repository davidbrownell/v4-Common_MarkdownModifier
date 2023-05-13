# ----------------------------------------------------------------------
# |
# |  DefinitionListPlugin_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-08 09:09:52
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit tests for DefinitionListPlugin.py"""

import re
import sys
import textwrap

from pathlib import Path
from unittest.mock import MagicMock as Mock

import pytest

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation import PathEx


# ----------------------------------------------------------------------
sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent.parent.parent)))
with ExitStack(lambda: sys.path.pop(0)):
    from Plugins.DefinitionListPlugin import Plugin as DefinitionListPlugin


# ----------------------------------------------------------------------
def test_Standard(_definition_list):
    _Execute(
        "",
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for <a href="#foo" data-definition-list-link=1>Foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  And here is <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?</div>
            </p>


            """,
        ),
        _definition_list,
    )


# ----------------------------------------------------------------------
def test_StandardWithPostprocessing(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for <a href="#foo" data-definition-list-link=1>Foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  And here is <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?</div>
            </p>

            <a href="#foo" data-definition-list-link=1>Foo</a>
            <a href="#foo" data-definition-list-link=1>Foo</a>'s
            <a href="#foo" data-definition-list-link=1>Foos</a>
            <a href="#foo" data-definition-list-link=1>Fooing</a>
            <a href="#foo" data-definition-list-link=1>Fooed</a>
            Fooey

            <a href="#bar" data-definition-list-link=1>Bar</a>
            bar
            <a href="#bar" data-definition-list-link=1>Bars</a>
            bars
            <a href="#bar" data-definition-list-link=1>Barring</a>
            <a href="#bar" data-definition-list-link=1>Barred</a>
            Bared
            Barific

            <a href="#one-two" data-definition-list-link=1>one two</a>
            <a href="#one-two" data-definition-list-link=1>one twoes</a>

            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-word</a>
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-wording</a>

            """,
        ),
        _definition_list,
    )


# ----------------------------------------------------------------------
def test_OldContentIsRemoved():
    _Execute(
        textwrap.dedent(
            """\
            <a href="#no-longer-exists" data-definition-list-link=1>No Longer Exists</a>
            foo
            """,
        ),
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">foo</a></i></div>
              <div>  A <a href="#foo" data-definition-list-link=1>foo</a>.</div>
            </p>

            No Longer Exists
            <a href="#foo" data-definition-list-link=1>foo</a>

            """,
        ),
        {
            "foo": "A foo.",
        },
    )


# ----------------------------------------------------------------------
def test_NoPostprocessingGlobal(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for Foo.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  And here is Bar.</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And hyphenated-words?</div>
            </p>

            Foo
            Foo's
            Foos
            Fooing
            Fooed
            Fooey

            Bar
            bar
            Bars
            bars
            Barring
            Barred
            Bared
            Barific

            one two
            one twoes

            hyphenated-word
            hyphenated-words?
            hyphenated-wording

            """,
        ),
        _definition_list,
        postprocess_type=DefinitionListPlugin.PostprocessType.NoPostprocessing,
    )


# ----------------------------------------------------------------------
def test_ExactGlobal(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for <a href="#foo" data-definition-list-link=1>Foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  And here is <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And hyphenated-words?</div>
            </p>

            <a href="#foo" data-definition-list-link=1>Foo</a>
            <a href="#foo" data-definition-list-link=1>Foo</a>'s
            Foos
            Fooing
            Fooed
            Fooey

            <a href="#bar" data-definition-list-link=1>Bar</a>
            bar
            Bars
            bars
            Barring
            Barred
            Bared
            Barific

            <a href="#one-two" data-definition-list-link=1>one two</a>
            one twoes

            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-word</a>
            hyphenated-words?
            hyphenated-wording

            """,
        ),
        _definition_list,
        postprocess_type=DefinitionListPlugin.PostprocessType.Exact,
    )


# ----------------------------------------------------------------------
def test_CaseInsensitiveGlobal(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for <a href="#foo" data-definition-list-link=1>Foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  And here is <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And hyphenated-words?</div>
            </p>

            <a href="#foo" data-definition-list-link=1>Foo</a>
            <a href="#foo" data-definition-list-link=1>Foo</a>'s
            Foos
            Fooing
            Fooed
            Fooey

            <a href="#bar" data-definition-list-link=1>Bar</a>
            <a href="#bar" data-definition-list-link=1>bar</a>
            Bars
            bars
            Barring
            Barred
            Bared
            Barific

            <a href="#one-two" data-definition-list-link=1>one two</a>
            one twoes

            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-word</a>
            hyphenated-words?
            hyphenated-wording

            """,
        ),
        _definition_list,
        postprocess_type=DefinitionListPlugin.PostprocessType.CaseInsensitive,
    )


# ----------------------------------------------------------------------
def test_StemmingExactGlobal(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for <a href="#foo" data-definition-list-link=1>Foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  And here is <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?</div>
            </p>

            <a href="#foo" data-definition-list-link=1>Foo</a>
            <a href="#foo" data-definition-list-link=1>Foo</a>'s
            <a href="#foo" data-definition-list-link=1>Foos</a>
            <a href="#foo" data-definition-list-link=1>Fooing</a>
            <a href="#foo" data-definition-list-link=1>Fooed</a>
            Fooey

            <a href="#bar" data-definition-list-link=1>Bar</a>
            bar
            <a href="#bar" data-definition-list-link=1>Bars</a>
            bars
            <a href="#bar" data-definition-list-link=1>Barring</a>
            <a href="#bar" data-definition-list-link=1>Barred</a>
            Bared
            Barific

            <a href="#one-two" data-definition-list-link=1>one two</a>
            <a href="#one-two" data-definition-list-link=1>one twoes</a>

            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-word</a>
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-wording</a>

            """,
        ),
        _definition_list,
        postprocess_type=DefinitionListPlugin.PostprocessType.Exact | DefinitionListPlugin.PostprocessType.Stemming,
    )


# ----------------------------------------------------------------------
def test_StemmingCaseInsensitiveGlobal(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for <a href="#foo" data-definition-list-link=1>Foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  And here is <a href="#bar" data-definition-list-link=1>Bar</a>.</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?</div>
            </p>

            <a href="#foo" data-definition-list-link=1>Foo</a>
            <a href="#foo" data-definition-list-link=1>Foo</a>'s
            <a href="#foo" data-definition-list-link=1>Foos</a>
            <a href="#foo" data-definition-list-link=1>Fooing</a>
            <a href="#foo" data-definition-list-link=1>Fooed</a>
            Fooey

            <a href="#bar" data-definition-list-link=1>Bar</a>
            <a href="#bar" data-definition-list-link=1>bar</a>
            <a href="#bar" data-definition-list-link=1>Bars</a>
            <a href="#bar" data-definition-list-link=1>bars</a>
            <a href="#bar" data-definition-list-link=1>Barring</a>
            <a href="#bar" data-definition-list-link=1>Barred</a>
            Bared
            Barific

            <a href="#one-two" data-definition-list-link=1>one two</a>
            <a href="#one-two" data-definition-list-link=1>one twoes</a>

            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-word</a>
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-wording</a>

            """,
        ),
        _definition_list,
        postprocess_type=DefinitionListPlugin.PostprocessType.CaseInsensitive | DefinitionListPlugin.PostprocessType.Stemming,
    )


# ----------------------------------------------------------------------
@pytest.mark.skip("Lemmatisation is not supported yet")
def test_LemmatisationExactGlobal(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            TODO
            """,
        ),
        _definition_list,
        postprocess_type=DefinitionListPlugin.PostprocessType.Exact | DefinitionListPlugin.PostprocessType.Lemmatisation,
    )


# ----------------------------------------------------------------------
@pytest.mark.skip("Lemmatisation is not supported yet")
def test_LemmatisationCaseInsensitiveGlobal(_content, _definition_list):
    _Execute(
        _content,
        textwrap.dedent(
            """\
            TODO
            """,
        ),
        _definition_list,
        postprocess_type=DefinitionListPlugin.PostprocessType.CaseInsensitive | DefinitionListPlugin.PostprocessType.Lemmatisation,
    )


# ----------------------------------------------------------------------
def test_CaseInsensitiveItem(_content, _definition_list):
    _definition_list["Bar"] = DefinitionListPlugin.DefinitionInfo(
        "A new definition",
        postprocess_type=DefinitionListPlugin.PostprocessType.CaseInsensitive,
    )

    _Execute(
        _content,
        textwrap.dedent(
            """\
            <p>
              <div><i><a id="foo">Foo</a></i></div>
              <div>  This is the definition for <a href="#foo" data-definition-list-link=1>Foo</a>.</div>
            </p>
            <p>
              <div><i><a id="bar">Bar</a></i></div>
              <div>  A new definition</div>
            </p>
            <p>
              <div><i><a id="one-two">one two</a></i></div>
              <div>  What happens when we search for multiple words?</div>
            </p>
            <p>
              <div><i><a id="hyphenated-word">hyphenated-word</a></i></div>
              <div>  And <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?</div>
            </p>

            <a href="#foo" data-definition-list-link=1>Foo</a>
            <a href="#foo" data-definition-list-link=1>Foo</a>'s
            <a href="#foo" data-definition-list-link=1>Foos</a>
            <a href="#foo" data-definition-list-link=1>Fooing</a>
            <a href="#foo" data-definition-list-link=1>Fooed</a>
            Fooey

            <a href="#bar" data-definition-list-link=1>Bar</a>
            <a href="#bar" data-definition-list-link=1>bar</a>
            Bars
            bars
            Barring
            Barred
            Bared
            Barific

            <a href="#one-two" data-definition-list-link=1>one two</a>
            <a href="#one-two" data-definition-list-link=1>one twoes</a>

            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-word</a>
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-words</a>?
            <a href="#hyphenated-word" data-definition-list-link=1>hyphenated-wording</a>

            """,
        ),
        _definition_list,
    )


# ----------------------------------------------------------------------
def test_ErrorPostprocessValues():
    with pytest.raises(
        ValueError,
        match=re.escape("Stemming/Lemmatisation must be used with a CaseInsensitive/Exact flag."),
    ):
        _Execute(
            "",
            "",
            {
                "Foo": DefinitionListPlugin.DefinitionInfo(
                    "The definition",
                    postprocess_type=DefinitionListPlugin.PostprocessType.Stemming,
                ),
            },
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@pytest.fixture
def _content() -> str:
    return textwrap.dedent(
        """\
        Foo
        Foo's
        Foos
        Fooing
        Fooed
        Fooey

        Bar
        bar
        Bars
        bars
        Barring
        Barred
        Bared
        Barific

        one two
        one twoes

        hyphenated-word
        hyphenated-words?
        hyphenated-wording
        """,
    )


# ----------------------------------------------------------------------
@pytest.fixture
def _definition_list() -> dict[str, str]:
    return {
        "Foo": "This is the definition for Foo.",
        "Bar": "And here is Bar.",
        "one two": "What happens when we search for multiple words?",
        "hyphenated-word": "And hyphenated-words?",
    }


# ----------------------------------------------------------------------
def _Execute(
    content: str,
    expected: str,
    *args,
    content_template: str=textwrap.dedent(
        """\
        {definitions}
        {content}
        """,
    ),
    **kwargs,
) -> None:
    plugin = DefinitionListPlugin()
    filename = Path("filename")

    assert plugin.Postprocess(
        filename,
        content_template.format(
            definitions=plugin.Execute(filename, *args, **kwargs),
            content=content,
        ),
    ).replace("&nbsp;", " ") == expected
