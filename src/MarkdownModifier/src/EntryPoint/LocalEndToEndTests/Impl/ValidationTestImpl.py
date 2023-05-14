# ----------------------------------------------------------------------
# |
# |  ValidationTestImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-14 10:53:09
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Functionality that implements the validation test"""

import subprocess

from pathlib import Path
from typing import TextIO


# ----------------------------------------------------------------------
def Validate(
    command_line_binary: str,
    input_dir: Path,
    output: TextIO,
) -> int:
    command_line = '{binary} Validate "{input_dir}"'.format(
        binary=command_line_binary,
        input_dir=input_dir,
    )

    output.write("Command Line: {}\n\n".format(command_line))

    result = subprocess.run(
        command_line,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    content = result.stdout.decode("UTF-8")

    output.write(content)

    return result.returncode
