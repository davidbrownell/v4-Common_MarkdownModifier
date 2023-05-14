# ----------------------------------------------------------------------
# |
# |  Standard_LocalEndToEndTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-14 10:27:05
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2023
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""End-to-end tests to invoke in the standard execution environment."""

import logging
import os
import sys
import unittest


# ----------------------------------------------------------------------
if os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY_CONFIGURATION") == "standard":
    # ----------------------------------------------------------------------
    class TestSuite(unittest.TestCase):
        # ----------------------------------------------------------------------
        def test_Standard(self):
            from io import StringIO
            from pathlib import Path

            from Common_Foundation import PathEx
            from Common_Foundation.Shell.All import CurrentShell

            from Impl.ValidationTestImpl import Validate

            sink = StringIO()

            assert Validate(
                "MarkdownModifier{}".format(CurrentShell.script_extensions[0]),
                PathEx.EnsureDir(Path(__file__).parent.parent.parent / "Examples"),
                sink,
            ) == 0

            sink = sink.getvalue()

            logger = logging.getLogger("TestSuite.test_Standard")

            logger.setLevel(logging.DEBUG)

            logger.info(sink)
            logger.info("\n\n")

            assert "No changes were detected." in sink


else:
    # Don't test anything in this configuration

    # ----------------------------------------------------------------------
    class TestSuitePlaceholder(unittest.TestCase):
        # ----------------------------------------------------------------------
        def test(self):
            assert True


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logging.basicConfig(stream=sys.stdout)

        sys.exit(
            unittest.main(
                verbosity=2,
            ),
        )
    except KeyboardInterrupt:
        pass
