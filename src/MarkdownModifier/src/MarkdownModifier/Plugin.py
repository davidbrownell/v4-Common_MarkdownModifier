# ----------------------------------------------------------------------
# |
# |  Plugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2023-05-03 12:01:53
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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from Common_Foundation.Types import extensionmethod


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Plugin(ABC):
    """Abstract base class for functionality implemented by a dynamically loaded plugin."""

    # ----------------------------------------------------------------------
    # |
    # |  Data
    # |
    # ----------------------------------------------------------------------
    name: str

    # ----------------------------------------------------------------------
    # |
    # |  Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    def CreateAnchorName(
        text: str,
    ) -> str:
        """Creates a valid anchor name given the provided text."""

        text = text.lower()

        for source, dest in [
            (" ", "-"),
            (".", ""),
        ]:
            text = text.replace(source, dest)

        return text

    # ----------------------------------------------------------------------
    @extensionmethod
    def Preprocess(
        self,
        filename: Path,  # pylint: disable=unused-argument
        content: str,
    ) -> str:
        """Decorates the content before cog has run"""

        # A plugin does not preprocess content by default
        return content

    # ----------------------------------------------------------------------
    @abstractmethod
    def Execute(
        self,
        filename: Path,
        *args,
        **kwargs,
    ) -> str:
        """Transforms the content; this functionality is invoked via cog"""
        raise Exception("Abstract method")  # pragma: no cover

    # ----------------------------------------------------------------------
    @extensionmethod
    def Postprocess(
        self,
        filename: Path,  # pylint: disable=unused-argument
        content: str,
    ) -> str:
        """Decorates the content after cog has run:"""

        # A plugin does not postprocess content by default
        return content

    # ----------------------------------------------------------------------
    @extensionmethod
    def Finalize(
        self,
        filename: Path,                     # pylint: disable=unused-argument
        content: str,                       # pylint: disable=unused-argument
    ) -> None:
        """Raise any errors based on teh generated content (if necessary)"""

        # A plugin does not do anything during finalization by default
        return None
