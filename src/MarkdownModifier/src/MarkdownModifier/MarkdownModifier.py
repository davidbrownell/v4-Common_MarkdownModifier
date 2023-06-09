# ----------------------------------------------------------------------
# |
# |  MarkdownModifier.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-11 10:35:46
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains functionality to modify Markdown content"""

import re

from enum import auto, Enum
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Match, Optional

from cogapp.cogapp import Cog

from .Plugin import Plugin


# ----------------------------------------------------------------------
class Status(Enum):
    """Used to communicate progress of the algorithm."""

    Preprocessing                           = auto()
    Transforming                            = auto()
    Postprocessing                          = auto()
    Finalizing                              = auto()


# ----------------------------------------------------------------------
def Modify(
    filename: Path,
    content: str,
    all_plugins: list[Plugin],
    on_status_update: Callable[[Status, str], None],
    *,
    include_plugin_names: Optional[set[str]]=None,
    exclude_plugin_names: Optional[set[str]]=None,
) -> str:
    include_plugin_names = include_plugin_names or set()
    exclude_plugin_names = exclude_plugin_names or set()

    # ----------------------------------------------------------------------
    def IsExcludedPlugin(
        plugin: Plugin,
    ) -> bool:
        return (
            (bool(exclude_plugin_names) and plugin.name in exclude_plugin_names)
            or (bool(include_plugin_names) and plugin.name not in include_plugin_names)
        )

    # ----------------------------------------------------------------------

    # Preprocess
    on_status_update(Status.Preprocessing, "Preprocessing...")

    for plugin in all_plugins:
        if IsExcludedPlugin(plugin):
            continue

        try:
            content = plugin.Preprocess(filename, content)
        except Exception as ex:
            raise Exception("{}: {}".format(plugin.name, ex)) from ex

    # Transform
    on_status_update(Status.Transforming, "Transforming...")

    cog = Cog()

    cog.options.sBeginSpec = "[[["
    cog.options.sEndSpec = "]]]"

    # ----------------------------------------------------------------------
    def CogWrapper(
        plugin: Plugin,
        *args,
        **kwargs,
    ) -> None:
        if IsExcludedPlugin(plugin):
            result = ""
        else:
            try:
                result = plugin.Execute(filename, *args, **kwargs)
            except Exception as ex:
                raise Exception("{}: {}".format(plugin.name, ex)) from ex

        cog.cogmodule.outl(result.rstrip())  # type: ignore  # pylint: disable=no-member

    # ----------------------------------------------------------------------

    # Create the globals made available to the plugin
    globals: dict[str, Any] = {}

    for plugin in all_plugins:
        globals[plugin.name] = lambda *args, plugin=plugin, **kwargs: CogWrapper(plugin, *args, **kwargs)
        globals["{}Type".format(plugin.name)] = plugin.__class__

    output = StringIO()

    cog.processFile(
        StringIO(content),
        output,
        globals=globals,
    )

    content = output.getvalue()

    # Postprocess
    on_status_update(Status.Postprocessing, "Postprocessing...")

    # Remove content from the output that we will never want replaced.
    scrubbed_placeholders: dict[str, str] = {}

    content = _ScrubCogSpecs(cog, content, scrubbed_placeholders)
    content = _ScrubUrls(content, scrubbed_placeholders)

    for plugin in all_plugins:
        if IsExcludedPlugin(plugin):
            continue

        try:
            content = plugin.Postprocess(filename, content)
        except Exception as ex:
            raise Exception("{}: {}".format(plugin.name, ex)) from ex

    if scrubbed_placeholders:
        content = re.sub(
            "|".join(re.escape(key) for key in scrubbed_placeholders.keys()),
            lambda match: scrubbed_placeholders[match.group(0)],
            content,
        )

    # Finalize
    on_status_update(Status.Finalizing, "Finalizing...")

    for plugin in all_plugins:
        if IsExcludedPlugin(plugin):
            continue

        try:
            plugin.Finalize(filename, content)
        except Exception as ex:
            raise Exception("{}: {}".format(plugin.name, ex)) from ex

    return content


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ScrubCogSpecs(
    cog: Cog,
    content: str,
    scrubbed_placeholders: dict[str, str],
) -> str:
    content_lines = content.split("\n")

    in_spec = False

    for line_index, line in enumerate(content_lines):
        should_scrub = False

        if cog.isBeginSpecLine(line) and not cog.isEndOutputLine(line):
            in_spec = True
            should_scrub = True

        if in_spec:
            should_scrub = True

            if cog.isEndSpecLine(line):
                in_spec = False

        if should_scrub:
            key = Plugin.CreatePlaceholderId()

            scrubbed_placeholders[key] = line
            content_lines[line_index] = key

    assert in_spec is False

    return "\n".join(content_lines)


# ----------------------------------------------------------------------
def _ScrubUrls(
    content: str,
    scrubbed_placeholders: dict[str, str],
) -> str:
    # ----------------------------------------------------------------------
    def Matcher(
        match: Match,
    ) -> str:
        key = Plugin.CreatePlaceholderId()

        scrubbed_placeholders[key] = match.group(0)
        return key

    # ----------------------------------------------------------------------

    return re.sub(
        r"""(?#
        (Prefix                             )[a-z]+(?#
        Delimiter                           ):\/\/(?#
        www                                 )(?:www\.)?(?#
        Domain                              )[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}(?#
        Suffix                              )\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)(?#
        )""",
        Matcher,
        content,
    )
