# ----------------------------------------------------------------------
# |
# |  MarkdownModifier.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-03 11:55:16
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

import sys

from pathlib import Path
from typing import List

from Common_Foundation import PathEx
from Common_Foundation import SubprocessEx


# ----------------------------------------------------------------------
def Execute(
    args: List[str],
) -> int:
    entry_point = PathEx.EnsureFile(Path(__file__).parent.parent / "src" / "MarkdownModifier" / "src" / "EntryPoint" / "__main__.py")

    command_line = 'python "{script}"{args}'.format(
        script=entry_point,
        args=" {}".format(" ".join('"{}"'.format(arg) for arg in args[1:])) if len(args) > 1 else "",
    )

    return SubprocessEx.Stream(command_line, sys.stdout)


# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(Execute(sys.argv))
