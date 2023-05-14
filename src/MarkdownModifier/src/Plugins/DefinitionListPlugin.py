# ----------------------------------------------------------------------
# |
# |  DefinitionListPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-03 12:41:01
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import re
import string
import textwrap

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import auto, IntFlag
from pathlib import Path
from typing import ClassVar, Match, Optional, Protocol, Union

from Common_Foundation import RegularExpression
from Common_Foundation.Types import overridemethod

from Common_FoundationEx.InflectEx import inflect

from MarkdownModifier.Plugin import Plugin as PluginBase  # type: ignore  # pylint: disable=import-error


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Plugin(PluginBase):
    """Plugin that creates a definition list of terms."""

    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------
    class PostprocessType(IntFlag):
        """Flags used to control how postprocessing is performed."""

        # Add links for content that...
        Exact                               = auto()    # ...is an exact match.
        CaseInsensitive                     = auto()    # ...is a case insensitive match.
        Stemming                            = auto()    # ...see https://en.wikipedia.org/wiki/Stemming
        Lemmatisation                       = auto()    # ...see https://en.wikipedia.org/wiki/Lemmatisation

        # Amalgamations
        NoPostprocessing                    = 0
        Default                             = CaseInsensitive | Stemming

    # ----------------------------------------------------------------------
    @dataclass(frozen=True)
    class DefinitionInfo(object):
        """Definition for a term."""

        definition: str

        anchor: Optional[str]                                               = field(kw_only=True, default=None)
        postprocess_type: Optional["Plugin.PostprocessType"]                = field(kw_only=True, default=None)

    # ----------------------------------------------------------------------
    class GenerateContentFuncType(Protocol):  # pylint: disable=missing-class-docstring
        def __call__(
            self,
            filename: Path,
            definitions: dict[str, "Plugin.DefinitionInfo"],
            *,
            indentation: int=2,
        ) -> str:
            ...  # pragma: no cover

    # ----------------------------------------------------------------------
    # |
    # |  Data
    # |
    # ----------------------------------------------------------------------
    name: ClassVar[str]                     = "DefinitionList"

    _postprocess_infos: list["Plugin._PostprocessInfo"]                     = field(init=False, default_factory=list)

    # ----------------------------------------------------------------------
    # |
    # |  Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    def DefaultGenerateContent(
        filename: Path,  # pylint: disable=unused-argument
        definitions: dict[str, "Plugin.DefinitionInfo"],
        *,
        indentation: int=2,
    ) -> str:
        indentation_value = "".join(["&nbsp;", ] * indentation)

        return "".join(
            textwrap.dedent(
                """\
                <p>
                  <div><i><a id="{anchor}">{key}</a></i></div>
                  <div>{indentation}{definition}</div>
                </p>
                """,
            ).format(
                anchor=value.anchor,
                key=key,
                indentation=indentation_value,
                definition=value.definition,
            )
            for key, value in definitions.items()
        )

    # ----------------------------------------------------------------------
    @overridemethod
    def Execute(
        self,
        filename: Path,
        definitions: dict[str, Union[str, "Plugin.DefinitionInfo"]],
        *,
        postprocess_type: PostprocessType=PostprocessType.Default,
        indentation: int=2,
        generate_content_func: GenerateContentFuncType=DefaultGenerateContent,
    ) -> str:
        resolved_definitions: dict[str, Plugin.DefinitionInfo] = {}

        for key, value in definitions.items():
            if isinstance(value, str):
                value = Plugin.DefinitionInfo(value)

            assert isinstance(value, Plugin.DefinitionInfo), value

            if value.anchor is None:
                object.__setattr__(value, "anchor", self.__class__.CreateAnchorName(key))

            assert value.anchor is not None

            resolved_definitions[key] = value

            this_postprocess_type = value.postprocess_type or postprocess_type

            if this_postprocess_type == Plugin.PostprocessType.NoPostprocessing:
                continue

            self._postprocess_infos.append(
                Plugin._PostprocessInfo(key, value.anchor, this_postprocess_type),
            )

        return generate_content_func(
            filename,
            resolved_definitions,
            indentation=indentation,
        )

    # ----------------------------------------------------------------------
    @overridemethod
    def Postprocess(
        self,
        filename: Path,  # pylint: disable=unused-argument
        content: str,
    ) -> str:
        link_template = '<a href="#{anchor}" data-definition-list-link=1>{text}</a>'

        # Remove previous content
        content = RegularExpression.TemplateStringToRegex(
            link_template,
            match_whole_string=False,
        ).sub(
            lambda match: match.group("text"),
            content,
        )

        # Create the data used to populate the content

        # ----------------------------------------------------------------------
        @dataclass(frozen=True)
        class Matcher(ABC):
            # ----------------------------------------------------------------------
            term: str
            anchor: str
            postprocess_type: Plugin.PostprocessType

            # ----------------------------------------------------------------------
            def Clone(
                self,
                term: str,
            ) -> "Matcher":
                return self.__class__(term, self.anchor, self.postprocess_type)

            # ----------------------------------------------------------------------
            @abstractmethod
            def CreateRegex(self) -> str:
                raise Exception("Abstract method")  # pragma: no cover

            # ----------------------------------------------------------------------
            @abstractmethod
            def MatchTerm(
                self,
                matching_text: str,
            ) -> bool:
                raise Exception("Abstract method")  # pragma: no cover

            # ----------------------------------------------------------------------
            def CreateLink(
                self,
                matching_text: str,
            ) -> str:
                return link_template.format(
                    anchor=self.anchor,
                    text=matching_text,
                )

        # ----------------------------------------------------------------------
        @dataclass(frozen=True)
        class CaseSensitiveMatcher(Matcher):
            # ----------------------------------------------------------------------
            @overridemethod
            def CreateRegex(self) -> str:
                return re.escape(self.term)

            # ----------------------------------------------------------------------
            @overridemethod
            def MatchTerm(
                self,
                matching_text: str,
            ) -> bool:
                return matching_text == self.term

        # ----------------------------------------------------------------------
        @dataclass(frozen=True)
        class CaseInsensitiveMatcher(Matcher):
            # ----------------------------------------------------------------------
            _lower_term: str                = field(init=False)

            # ----------------------------------------------------------------------
            def __post_init__(self):
                object.__setattr__(self, "_lower_term", self.term.lower())

            # ----------------------------------------------------------------------
            @overridemethod
            def CreateRegex(self) -> str:
                return r"(?i:{})".format(re.escape(self.term))

            # ----------------------------------------------------------------------
            @overridemethod
            def MatchTerm(
                self,
                matching_text: str,
            ) -> bool:
                return matching_text.lower() == self._lower_term

        # ----------------------------------------------------------------------

        matchers: list[Matcher] = []
        ngram_terms: list[list[str]] = []

        stemming_items: list[Plugin._PostprocessInfo] = []
        lemmatisation_items: list[Plugin._PostprocessInfo] = []

        for pi in self._postprocess_infos:
            prev_matchers_len = len(matchers)

            if pi.postprocess_type & Plugin.PostprocessType.CaseInsensitive:
                matchers.append(CaseInsensitiveMatcher(pi.term, pi.anchor, pi.postprocess_type))
            elif pi.postprocess_type & Plugin.PostprocessType.Exact:
                matchers.append(CaseSensitiveMatcher(pi.term, pi.anchor, pi.postprocess_type))

            if (
                pi.postprocess_type & Plugin.PostprocessType.Stemming
                or pi.postprocess_type & Plugin.PostprocessType.Lemmatisation
            ):
                added_matcher = len(matchers) != prev_matchers_len

                if not added_matcher:
                    raise ValueError("Stemming/Lemmatisation must be used with a CaseInsensitive/Exact flag.")

                if pi.postprocess_type & Plugin.PostprocessType.Stemming:
                    stemming_items.append(pi)
                if pi.postprocess_type & Plugin.PostprocessType.Lemmatisation:
                    # TODO lemmatisation_items.append(pi)
                    pass # pragma: no cover

                if " " in pi.term:
                    ngram_terms.append(pi.term.split(" "))

                    # As a convenience, attempt to create the plural version of this ngram.
                    # I don't like this code, as what we really need is reverse stemming. Furthermore,
                    # doing this is a slippery slope as what happens when we need to support other stem
                    # suffixes. Unfortunately, it doesn't seem like nltk provides this functionality
                    # so we are doing the most common cases here.
                    trailing_token = inflect.plural(ngram_terms[-1][-1])
                    if trailing_token != ngram_terms[-1][-1]:
                        ngram_terms.append(ngram_terms[-1][:-1] + [trailing_token, ])

        if stemming_items or lemmatisation_items:
            original_matchers_len = len(matchers)

            from nltk.tokenize import MWETokenizer

            # Is this code necessary?
            # for module in [
            #     "punkt",
            # ]:
            #     nltk.download(
            #         module,
            #         download_dir=nltk.data.path[0],
            #     )

            # Remove the punctuation from the content
            replacement_map: dict[str, str] = {
                char: "" for char in string.punctuation if char not in ["<", ">", "-"]
            }

            replacement_map["&nbsp;"] = " "
            replacement_map["<"] = " <"
            replacement_map[">"] = "> "

            tokenize_content = re.sub(
                "|".join(re.escape(key) for key in replacement_map.keys()),
                lambda match: replacement_map[match.group(0)],
                content,
            )

            tokens = MWETokenizer(
                ngram_terms,
                separator=" ",
            ).tokenize(tokenize_content.split())

            if stemming_items:
                from nltk.stem.porter import PorterStemmer

                stemmer = PorterStemmer()
                processed_tokens: set[str] = set(matcher.term for matcher in matchers)

                for token in tokens:
                    if token in processed_tokens:
                        continue

                    processed_tokens.add(token)

                    stemmed_token = stemmer.stem(token)

                    # Stemmed tokens will always be lower case, but we want to maintain
                    # the case of the original token whenever we can.
                    if token[0].isupper():
                        stemmed_upper = stemmed_token[0].upper()
                        if stemmed_upper == token[0]:
                            stemmed_token = "{}{}".format(stemmed_upper, stemmed_token[1:])

                    matcher = next(
                        (
                            matcher
                            for matcher in matchers[:original_matchers_len]
                            if (
                                matcher.postprocess_type & Plugin.PostprocessType.Stemming
                                and matcher.MatchTerm(stemmed_token)
                            )
                        ),
                        None,
                    )
                    if matcher is None:
                        continue

                    matchers.append(matcher.Clone(token))

            if lemmatisation_items:
                raise Exception("TODO: Not implemented yet")  # pragma: no cover

        # Populate the content
        if not matchers:
            return content

        # ----------------------------------------------------------------------
        def Sub(
            match: Match,
        ) -> str:
            matcher = next((matcher for matcher in matchers if matcher.MatchTerm(match.group(0))))
            return matcher.CreateLink(content[match.start():match.end()])

        # ----------------------------------------------------------------------

        content = re.sub(
            r"""(?#
            Don't match when following a tag            )(?<!\>)(?#
            Don't match an anchor                       )(?<!id=")(?#
            Word boundary                               )\b(?#
            Regex                                       )(?:{})(?#
            Word boundary                               )\b(?#
            Don't match if followed by a tag            )(?!\<)(?#
            )""".format(
                "|".join(matcher.CreateRegex() for matcher in matchers),
            ),
            Sub,
            content,
        )

        return content

    # ----------------------------------------------------------------------
    # |
    # |  Private Data
    # |
    # ----------------------------------------------------------------------
    @dataclass(frozen=True)
    class _PostprocessInfo(object):
        term: str
        anchor: str
        postprocess_type: "Plugin.PostprocessType"
