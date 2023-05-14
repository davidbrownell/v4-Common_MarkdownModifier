# ----------------------------------------------------------------------
# |
# |  BuildVerification_LocalEndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-14 10:15:11
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Build verification test for MarkdownModifier and"""

import stat
import subprocess
import sys
import textwrap

from pathlib import Path

from Impl.ValidationTestImpl import Validate

# ----------------------------------------------------------------------
def EntryPoint(
    args: list[str],
) -> int:
    if len(args) != 2:
        sys.stdout.write(
            textwrap.dedent(
                """\
                ERROR: Usage:

                    {} <temp_directory>

                """,
            ).format(args[0]),
        )

        return -1


    temp_directory = Path(args[1])
    assert temp_directory.is_dir(), temp_directory

    # Get the binary
    binary = Path(temp_directory) / "MarkdownModifier"

    if not binary.is_file():
        potential_binary = binary.with_suffix(".exe")

        if potential_binary.is_file():
            binary = potential_binary

    if not binary.is_file():
        raise Exception("The filename '{}' does not exist.\n".format(binary))

    # https://github.com/actions/upload-artifact/issues/38
    # Permissions are not currently being saved when uploading artifacts, so they must be set here.
    # This will eventually be fixed, which is why I am placing the work around here rather than in
    # the artifact upload- or download-code.
    binary.chmod(stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)

    return Validate(
        str(binary),
        temp_directory / "Examples",
        sys.stdout,
    )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(EntryPoint(sys.argv))
