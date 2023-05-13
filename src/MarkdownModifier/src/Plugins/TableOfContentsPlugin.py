# ----------------------------------------------------------------------
# |
# |  TableOfContentsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-08 09:15:23
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

import uuid
import re

from dataclasses import dataclass, field, InitVar
from enum import auto, Enum
from pathlib import Path
from typing import Callable, cast, ClassVar, Iterable, Iterator, Optional, Union

from Common_Foundation.Types import overridemethod

from MarkdownModifier.Plugin import Plugin as PluginBase


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Plugin(PluginBase):
    """Plugin that generates a table of contents based on headings within a page."""

    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------
    SIMPLE_SYMBOLS: ClassVar[list[str]]     = ["-", "*", ".", ]
    UNKNOWN_HEADING_NAME: ClassVar[str]     = "Unknown"

    # ----------------------------------------------------------------------
    @dataclass(frozen=True)
    class LineItemInfo(object):
        """Information about a table of contents line item."""

        prefix: str
        text: str
        anchor: Optional[str]

    # ----------------------------------------------------------------------
    class LineItemPrefixType(Enum):
        """Identifiers for predefined algorithms for generating table of contents line items."""

        Numeric                             = auto()    # 1, 1.1, 1.1.1, ...
        Simple                              = auto()    # Generates based on SIMPLE_SYMBOLS

    # ----------------------------------------------------------------------
    @dataclass(frozen=True)
    class HeadingInfo(object):
        """Information about a heading used when generating table of contents line items."""

        text: str
        level: int
        index: int

    # ----------------------------------------------------------------------
    LineItemPrefixStrategyType              = Union[
        "Plugin.LineItemPrefixType",                    # Use a predefined strategy
        list[str],                                      # Use the heading's level to map to a value within the list
        Callable[[list[HeadingInfo]], str],             # Call the function to determine the line item prefix
    ]

    # ----------------------------------------------------------------------
    GenerateTableOfContentsFuncType         = Callable[
        [
            Path,
            Iterable[LineItemInfo],
        ],
        str,
    ]

    # ----------------------------------------------------------------------
    # |
    # |  Data
    # |
    # ----------------------------------------------------------------------
    name: ClassVar[str]                     = "TableOfContents"

    _sections: dict[str, "Plugin._Options"] = field(init=False, default_factory=dict)

    # ----------------------------------------------------------------------
    # |
    # |  Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    def DefaultGenerateTableOfContents(
        filename: Path,  # pylint: disable=unused-argument
        line_items: Iterable[LineItemInfo],
    ) -> str:
        contents: list[str] = []

        for line_item in line_items:
            content = line_item.text

            if line_item.anchor is not None:
                content = '<a href="#{}">{}</a>'.format(line_item.anchor, content)

            content = "<div>{}{}{}</div>".format(
                line_item.prefix.replace(" ", "&nbsp;"),
                " " if line_item.prefix else "",
                content,
            )

            contents.append(content)

        return "\n".join(contents)

    # ----------------------------------------------------------------------
    @overridemethod
    def Execute(
        self,
        filename: Path,  # pylint: disable=unused-argument
        *,
        heading_min: int=1,
        heading_max: int=6,
        indentation: int=2,
        line_item_prefix_strategy: LineItemPrefixStrategyType=LineItemPrefixType.Numeric,
        generate_table_of_contents_func: GenerateTableOfContentsFuncType=DefaultGenerateTableOfContents,
        unknown_heading_name: str=UNKNOWN_HEADING_NAME,
    ) -> str:
        # Defer processing, as other plugins might generate content that should be included in the
        # output of this plugin.
        unique_id = "{}{}".format(
            str(uuid.uuid4()).replace("-", ""),
            str(uuid.uuid4()).replace("-", ""),
        )

        self._sections[unique_id] = Plugin._Options(
            heading_min,
            heading_max,
            indentation,
            line_item_prefix_strategy,
            generate_table_of_contents_func,
            unknown_heading_name,
        )

        return str(unique_id)

    # ----------------------------------------------------------------------
    @overridemethod
    def Postprocess(
        self,
        filename: Path,
        content: str,
    ) -> str:
        # Extract the headings

        # ----------------------------------------------------------------------
        @dataclass(frozen=True)
        class ExtractedHeading(object):
            level: int
            text: str
            anchor: str

        # ----------------------------------------------------------------------

        headings: list[ExtractedHeading] = []

        for match in re.finditer(
            r"""(?#
            Beginning of line               )^(?#
            Initial whitespace              )\s*(?#
            Heading level                   )(?P<level>\#+)\s*(?#
            Text                            )(?P<text>.+?)\s*(?#
            Explicit anchor name            )(?:\{\#(?P<anchor>.+)\})?(?#
            End of line                     )$(?#
            )""",
            content,
            re.MULTILINE,
        ):
            text = match.group("text")

            headings.append(
                ExtractedHeading(
                    len(match.group("level")),
                    text,
                    match.group("anchor") or self.__class__.CreateAnchorName(text),
                ),
            )

        # Populate the placeholder content
        for unique_id, options in self._sections.items():
            # ----------------------------------------------------------------------
            def GenerateLineItems() -> Iterator[Plugin.LineItemInfo]:
                # ----------------------------------------------------------------------
                @dataclass(frozen=True)
                class HeadingInfoEx(Plugin.HeadingInfo):
                    # ----------------------------------------------------------------------
                    was_generated: bool     = field(init=False, default=False)

                    # ----------------------------------------------------------------------
                    def CreateLineItemInfo(
                        self,
                        prefix: str,
                        anchor: Optional[str],
                    ) -> Plugin.LineItemInfo:
                        assert self.was_generated is False
                        object.__setattr__(self, "was_generated", True)

                        return Plugin.LineItemInfo(
                            prefix,
                            self.text,
                            anchor,
                        )

                # ----------------------------------------------------------------------

                heading_infos: list[HeadingInfoEx] = []
                heading_counters: list[int] = []

                for heading in headings:
                    if heading.level > options.heading_max:
                        continue

                    while heading_infos and heading.level <= heading_infos[-1].level:
                        heading_infos.pop()

                    added_counters = False

                    if len(heading_counters) < heading.level:
                        heading_counters += [0, ] * (heading.level - len(heading_counters))

                        added_counters = True

                    elif len(heading_counters) > heading.level:
                        heading_counters = heading_counters[:heading.level]

                    heading_counters[heading.level - 1] += 1

                    if added_counters:
                        # Ensure that all heading counters are populated
                        for index in range(len(heading_counters)):
                            if heading_counters[index] != 0:
                                continue

                            heading_counters[index] = 1

                            heading_infos.insert(
                                index,
                                HeadingInfoEx(
                                    options.unknown_heading_name,
                                    index + 1,
                                    heading_counters[index],
                                ),
                            )

                    heading_infos.append(
                        HeadingInfoEx(
                            heading.text,
                            heading.level,
                            heading_counters[heading.level - 1],
                        ),
                    )

                    if heading.level < options.heading_min:
                        continue

                    # Send any line items that haven't been sent yet
                    for index in range(options.heading_min, len(heading_infos) - 1):
                        heading_info = heading_infos[index]

                        if heading_info.was_generated:
                            continue

                        yield heading_info.CreateLineItemInfo(
                            options.line_item_prefix_func(cast(list[Plugin.HeadingInfo], heading_infos[:index + 1])),
                            None,
                        )

                    yield heading_infos[-1].CreateLineItemInfo(
                        options.line_item_prefix_func(cast(list[Plugin.HeadingInfo], heading_infos)),
                        heading.anchor,
                    )

            # ----------------------------------------------------------------------

            table_of_contents = options.generate_table_of_contents_func(filename, GenerateLineItems())

            content = content.replace(unique_id, table_of_contents)

        return content

    # ----------------------------------------------------------------------
    # |
    # |  Private Types
    # |
    # ----------------------------------------------------------------------
    @dataclass(frozen=True)
    class _Options(object):
        # ----------------------------------------------------------------------
        heading_min: int
        heading_max: int
        indentation: int

        line_item_prefix_strategy: InitVar["Plugin.LineItemPrefixStrategyType"]
        line_item_prefix_func: Callable[[list["Plugin.HeadingInfo"]], str]          = field(init=False)

        generate_table_of_contents_func: "Plugin.GenerateTableOfContentsFuncType"

        unknown_heading_name: str

        # ----------------------------------------------------------------------
        def __post_init__(
            self,
            line_item_prefix_strategy: "Plugin.LineItemPrefixStrategyType",
        ) -> None:
            if self.heading_min < 1:
                raise ValueError("heading values must be >= 1.")
            if self.heading_max < self.heading_min:
                raise ValueError("min heading values must be <= max heading values.")

            if self.indentation < 0:
                raise ValueError("indentation values must be >= 0.")

            if isinstance(line_item_prefix_strategy, Plugin.LineItemPrefixType):
                if line_item_prefix_strategy == Plugin.LineItemPrefixType.Numeric:
                    line_item_prefix_strategy = lambda headings: ".".join(str(heading.index) for heading in headings)
                elif line_item_prefix_strategy == Plugin.LineItemPrefixType.Simple:
                    line_item_prefix_strategy = Plugin.SIMPLE_SYMBOLS
                else:
                    assert False, line_item_prefix_strategy  # pragma: no cover

            if isinstance(line_item_prefix_strategy, list):
                expected_values = self.heading_max - self.heading_min + 1
                actual_values = len(line_item_prefix_strategy)

                if actual_values > expected_values:
                    line_item_prefix_strategy = line_item_prefix_strategy[:expected_values]
                elif actual_values < expected_values:
                    raise ValueError(
                        "{} line item prefix values were expected but {} were provided.".format(
                            expected_values,
                            actual_values,
                        ),
                    )

                original_line_item_prefix_values = line_item_prefix_strategy

                # ----------------------------------------------------------------------
                def LineItemPrefixFromList(
                    headings: list[Plugin.HeadingInfo],
                ) -> str:
                    return original_line_item_prefix_values[len(headings) - 1]

                # ----------------------------------------------------------------------

                line_item_prefix_strategy = LineItemPrefixFromList

            assert callable(line_item_prefix_strategy), line_item_prefix_strategy

            whitespaces: list[str] = [" " * (index * self.indentation) for index in range(self.heading_max - self.heading_min + 1)]

            # ----------------------------------------------------------------------
            def LineItemPrefix(
                headings: list[Plugin.HeadingInfo],
            ) -> str:
                return "{}{}".format(
                    whitespaces[headings[-1].level - self.heading_min],
                    line_item_prefix_strategy(headings),
                )

            # ----------------------------------------------------------------------

            object.__setattr__(self, "line_item_prefix_func", LineItemPrefix)
