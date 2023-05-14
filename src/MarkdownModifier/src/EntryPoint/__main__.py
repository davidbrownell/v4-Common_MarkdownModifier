# ----------------------------------------------------------------------
# |
# |  __main__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-03 12:00:04
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Augments a markdown file (or collection of files)."""

import importlib
import re
import sys
import textwrap
import traceback

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Callable, cast, Optional, Pattern

from Common_Foundation.ContextlibEx import ExitStack
from Common_Foundation.EnumSource import EnumSource
from Common_Foundation import PathEx
from Common_Foundation.Streams.DoneManager import DoneManager, DoneManagerFlags
from Common_Foundation import TextwrapEx

from Common_FoundationEx import ExecuteTasks
from Common_FoundationEx.InflectEx import inflect

# typer must be imported after the imports above
import typer

from typer.core import TyperGroup

# The following imports aren't used here, but are necessary to ensure that the standard plugins work
# as expected.
from Common_Foundation import RegularExpression         # pylint: disable=unused-import


# ----------------------------------------------------------------------
sys.path.insert(0, str(PathEx.EnsureDir(Path(__file__).parent.parent)))
with ExitStack(lambda: sys.path.pop(0)):
    # This configuration (in terms of the items listed below) is the only way that I could get
    # this to work both locally and when frozen as an executable, here and with plugins.
    #
    # Modify at your own risk.
    #
    #   Factors that contributed to this configuration:
    #
    #       - Directory name (which is why there is the funky 'src/MarkdownModifier/src/MarkdownModifier' layout
    #       - This file as 'EntryPoint/__main__.py' rather than '../EntryPoint.py'
    #       - Build.py/setup.py located outside of 'src'

    from MarkdownModifier.MarkdownModifier import Modify, Status
    from MarkdownModifier.Plugin import Plugin                              # pylint: disable=import-error


# ----------------------------------------------------------------------
def _LoadPlugins() -> dict[str, Plugin]:
    # Ensure that the MarkdownModifier directory is accessible on the path
    lib_dir = PathEx.EnsureDir(Path(__file__).parent.parent / "MarkdownModifier")

    sys.path.insert(0, str(lib_dir))
    with ExitStack(lambda: sys.path.pop(0)):
        plugin_dir = Path(__file__).parent.parent / "Plugins"
        if not plugin_dir.is_dir():
            raise Exception("The plugin directory '{}' does not exist.".format(plugin_dir))

        sys.path.insert(0, str(plugin_dir))
        with ExitStack(lambda: sys.path.pop(0)):
            # ----------------------------------------------------------------------
            @dataclass(frozen=True)
            class PluginData(object):
                filename: Path
                plugin: Plugin

            # ----------------------------------------------------------------------

            potential_plugin_names: list[str] = ["Plugin", ]

            all_plugins: dict[str, PluginData] = {}

            for filename in plugin_dir.iterdir():
                if filename.suffix != ".py":
                    continue

                if not filename.stem.endswith("Plugin"):
                    continue

                mod = importlib.import_module(filename.stem)

                plugin: Optional[Plugin] = None

                for potential_plugin_name in potential_plugin_names:
                    potential_plugin = getattr(mod, potential_plugin_name, None)
                    if potential_plugin is None:
                        continue

                    plugin = cast(Plugin, potential_plugin())
                    break

                if plugin is None:
                    raise Exception("A plugin was not found in '{}'.".format(filename))

                prev_plugin = all_plugins.get(plugin.name, None)
                if prev_plugin is not None:
                    raise Exception(
                        "The plugin '{}', defined in '{}', was already defined in '{}'.".format(
                            plugin.name,
                            filename,
                            prev_plugin.filename,
                        ),
                    )

                all_plugins[plugin.name] = PluginData(filename, plugin)

            if not all_plugins:
                raise Exception("No plugins were found in '{}'.".format(plugin_dir))

            # If here, all plugins are valid and there weren't any conflicts
            return {k: v.plugin for k, v in all_plugins.items()}


_PLUGINS                                    = _LoadPlugins()

del _LoadPlugins


# ----------------------------------------------------------------------
class NaturalOrderGrouper(TyperGroup):
    # ----------------------------------------------------------------------
    def list_commands(self, *args, **kwargs):  # pylint: disable=unused-argument
        return self.commands.keys()


# ----------------------------------------------------------------------
def _HelpEpilog() -> str:
    return textwrap.dedent(
        """\

        Plugins:

            {}

        """,
    ).format(
        TextwrapEx.Indent(
            TextwrapEx.CreateTable(
                ["Name", "Description"],
                [
                    [plugin.name, plugin.__doc__ or ""]
                    for plugin in _PLUGINS.values()
                ],
            ),
            4,
            skip_first_line=True,
        ),
    ).replace("\n", "\n\n")


# ----------------------------------------------------------------------
app                                         = typer.Typer(
    cls=NaturalOrderGrouper,
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="rich",
    epilog=_HelpEpilog(),
)


# ----------------------------------------------------------------------
def _ValidatePluginNames(
    names: list[str],
) -> list[str]:
    for name in names:
        if name not in _PLUGINS:
            raise typer.BadParameter("'{}' is not a valid plugin name.".format(name))

    return names


# ----------------------------------------------------------------------
_input_file_or_directory_argument           = typer.Argument(..., exists=True, resolve_path=True, help="Input filename or directory to search for files.")

_include_filename_option                    = typer.Option(None, "--include-filename", help="Regular expression matching filenames to include; can be specified multiple times on the command line.")
_exclude_filename_option                    = typer.Option(None, "--exclude-filename", help="Regular expression matching filenames to exclude; can be specified multiple times on the command line.")

_include_plugins_option                     = typer.Option(None, "--include-plugin", callback=_ValidatePluginNames, help="Name of a plugin to include when modifying markdown content; can be specified multiple times on the command line.")
_exclude_plugins_option                     = typer.Option(None, "--exclude-plugin", callback=_ValidatePluginNames, help="Name of a plugin to exclude when modifying markdown content; can be specified multiple times on the command line.")

_quiet_option                               = typer.Option(False, "--quiet", help="Reduce the amount of information written to the terminal.")
_verbose_option                             = typer.Option(False, "--verbose", help="Write verbose information to the terminal.")
_debug_option                               = typer.Option(False, "--debug", help="Write debug information to the terminal.")


# ----------------------------------------------------------------------
@app.command(
    "Execute",
    epilog=_HelpEpilog(),
    no_args_is_help=True,
)
def Execute(
    input_file_or_directory: Path=_input_file_or_directory_argument,
    include_filenames: list[str]=_include_filename_option,
    exclude_filenames: list[str]=_exclude_filename_option,
    include_plugins: list[str]=_include_plugins_option,
    exclude_plugins: list[str]=_exclude_plugins_option,
    quiet: bool=_quiet_option,
    verbose: bool=_verbose_option,
    debug: bool=_debug_option,
) -> None:
    """Modifies markdown files."""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        results = _Transform(
            dm,
            input_file_or_directory,
            include_filenames=include_filenames or None,
            exclude_filenames=exclude_filenames or None,
            include_plugins=include_plugins or None,
            exclude_plugins=exclude_plugins or None,
            quiet=quiet,
        )

        if not results or dm.result != 0:
            return

        dm.WriteLine(
            "\n{} modified.\n\n".format(
                inflect.no("markdown file", sum(1 if k else 0 for k in results.values())),
            ),
        )

        if dm.is_verbose:
            dm.WriteLine("")

            for k, v in results.items():
                dm.WriteInfo("{}: {}\n".format(k, "Modified" if v else "Unmodified"))

            dm.WriteLine("")

        for k, v in results.items():
            if v is None:
                continue

            with dm.Nested("Updating '{}'...".format(k)):
                with k.open("w", encoding="UTF-8") as f:
                    f.write(v)


# ----------------------------------------------------------------------
@app.command(
    "Validate",
    epilog=_HelpEpilog(),
    no_args_is_help=True,
)
def Validate(
    input_file_or_directory: Path=_input_file_or_directory_argument,
    include_filenames: list[str]=_include_filename_option,
    exclude_filenames: list[str]=_exclude_filename_option,
    include_plugins: list[str]=_include_plugins_option,
    exclude_plugins: list[str]=_exclude_plugins_option,
    quiet: bool=_quiet_option,
    verbose: bool=_verbose_option,
    debug: bool=_debug_option,
) -> None:
    """Causes an error if any files would be modified when processing the markdown files."""

    with DoneManager.CreateCommandLine(
        output_flags=DoneManagerFlags.Create(verbose=verbose, debug=debug),
    ) as dm:
        results = _Transform(
            dm,
            input_file_or_directory,
            include_filenames=include_filenames or None,
            exclude_filenames=exclude_filenames or None,
            include_plugins=include_plugins or None,
            exclude_plugins=exclude_plugins or None,
            quiet=quiet,
        )

        if dm.result != 0:
            return

        dm.WriteLine("")

        for k, v in results.items():
            if not v:
                continue

            dm.WriteLine("Changes were detected in '{}'.\n".format(k))
            dm.result = 1

        if dm.result == 0:
            dm.WriteLine("No changes were detected.\n")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Transform(
    dm: DoneManager,
    input_file_or_directory: Path,
    *,
    include_filenames: Optional[list[str]],
    exclude_filenames: Optional[list[str]],
    include_plugins: Optional[list[str]],
    exclude_plugins: Optional[list[str]],
    quiet: bool,
) -> dict[Path, Optional[str]]:
    filenames: list[Path] = _GetFilenames(
        dm,
        input_file_or_directory,
        include_filenames,
        exclude_filenames,
    )

    if not filenames:
        dm.WriteLine("No markdown files were found.\n")
        return {}

    if dm.result != 0:
        return {}

    plugins = list(_PLUGINS.values())

    # ----------------------------------------------------------------------
    def TransformStep1(
        context: Path,
        on_simple_status_func: Callable[[str], None],  # pylint: disable=unused-argument
    ) -> tuple[Optional[int], ExecuteTasks.TransformStep2FuncType]:
        filename = context
        del context

        # ----------------------------------------------------------------------
        def Step2(
            status: ExecuteTasks.Status,  # pylint: disable=unused-argument
        ) -> tuple[Optional[str], Optional[str]]:
            with filename.open(encoding="UTF-8") as f:
                content = f.read()

            original_content = content

            content = Modify(
                filename,
                content,
                plugins,
                lambda status_id, text: cast(None, status.OnProgress(status_id.value, text)),
                include_plugin_names=set(include_plugins or []),
                exclude_plugin_names=set(exclude_plugins or []),
            )

            if content == original_content:
                content = None
                status_text = "No updates"
            else:
                status_text = None

            return content, status_text

        # ----------------------------------------------------------------------

        return len(Status), Step2

    # ----------------------------------------------------------------------

    results: dict[Path, Optional[str]] = {}

    for filename, content in zip(
        filenames,
        ExecuteTasks.Transform(
            dm,
            "Transforming",
            [ExecuteTasks.TaskData(str(filename), filename) for filename in filenames],
            TransformStep1,
            quiet=quiet,
            max_num_threads=1, # Note that cogapp is not thread safe as it is overwriting sys.stdout and sys.stderr
            return_exceptions=True,
        ),
    ):
        if isinstance(content, Exception):
            if dm.is_debug:
                sink = StringIO()

                traceback.print_exception(content, file=sink)

                error = sink.getvalue()
            else:
                error = str(content)

            dm.WriteError(
                textwrap.dedent(
                    """\
                    {}
                        {}

                    """,
                ).format(
                    filename,
                    TextwrapEx.Indent(
                        error.rstrip(),
                        4,
                        skip_first_line=True,
                    ),
                ),
            )

            continue

        results[filename] = content

    return results


# ----------------------------------------------------------------------
def _GetFilenames(
    dm: DoneManager,
    input_file_or_directory: Path,
    include_filenames_param: Optional[list[str]],
    exclude_filenames_param: Optional[list[str]],
) -> list[Path]:
    # ----------------------------------------------------------------------
    def ToRegularExpressions(
        expressions: Optional[list[str]],
    ) -> Optional[list[Pattern]]:
        if expressions is None:
            return None

        results: list[Pattern] = []

        for expression in expressions:
            try:
                results.append(re.compile(expression))
            except re.error as ex:
                raise typer.BadParameter(
                    "'{}' is not a valid regular expression: {}.".format(expression, ex),
                )

        return results

    # ----------------------------------------------------------------------

    include_filenames = ToRegularExpressions(include_filenames_param)
    exclude_filenames = ToRegularExpressions(exclude_filenames_param)
    # Get the files
    all_filenames: list[Path] = []

    if input_file_or_directory.is_file():
        all_filenames.append(input_file_or_directory)
    elif input_file_or_directory.is_dir():
        with dm.Nested(
            "Searching for markdown files in '{}'...".format(input_file_or_directory),
            lambda: "{} found".format(inflect.no("file", len(all_filenames))),
            suffix="\n",
        ) as search_dm:
            for root, _, filenames in EnumSource(input_file_or_directory):
                for filename in filenames:
                    fullpath = root / filename

                    if fullpath.suffix != ".md":
                        continue

                    search_dm.WriteVerbose("'{}' found.\n".format(fullpath))
                    all_filenames.append(fullpath)

    else:
        assert False, input_file_or_directory  # pragma: no cover

    # Filter the files

    # ----------------------------------------------------------------------
    def IsExcludedFile(
        filename: Path,
    ) -> bool:
        filename_string = str(filename)

        return (
            (bool(exclude_filenames) and any(expression.match(filename_string) for expression in exclude_filenames))
            or (bool(include_filenames) and not any(expression.match(filename_string) for expression in include_filenames))
        )

    # ----------------------------------------------------------------------

    all_filenames = [filename for filename in all_filenames if not IsExcludedFile(filename)]

    return all_filenames


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
