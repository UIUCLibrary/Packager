"""Transforming one collection type into another."""

import abc
import logging
import os
import shutil
from typing import Optional
from py3exiv2bind.core import set_dpi
try:
    import pykdu_compress
except ImportError:
    print("Unable to use transform DigitalLibraryCompound due to "
          "missing import")


class AbsTransformation(metaclass=abc.ABCMeta):
    """Abstract base class for creating transformation classes.

    Perform some form of operation on a file, such as convert or copy
    """

    @abc.abstractmethod
    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> str:
        """Perform some transformation.

        Args:
            source: File path to source file
            destination: File path to save new file
            logger: System logger. For debugging or passing processing data

        """


class CopyFile(AbsTransformation):
    """CopyFile."""

    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> str:
        """Perform the transform.

        Args:
            source:
            destination:
            logger: System logger. For debugging or passing processing data

        """
        dest = os.path.abspath(os.path.dirname(destination))
        source_name = os.path.basename(source)

        logger.debug("Copying {} to {}".format(source_name, dest))
        shutil.copy(source, destination)
        return os.path.join(dest, source_name)
        # logger.info("Added {} to {}".format(source_name, dest))


class ConvertTiff(AbsTransformation):
    """ConvertTiff."""

    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> str:
        """Transform tiff.

        Args:
            source:
            destination:
            logger: System logger. For debugging or passing processing data

        """
        base_name = os.path.splitext(source)[0]
        new_name = f"{base_name}.tif"
        dest = os.path.abspath(os.path.dirname(destination))

        pykdu_compress.kdu_expand_cli(infile=source, outfile=destination)
        logger.info("Generated {} in {}".format(new_name, dest))
        return new_name


class ConvertJp2Standard(AbsTransformation):
    """ConvertJp2Standard."""

    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> str:
        """Transform standard jp200.

        Args:
            source:
            destination:
            logger: System logger. For debugging or passing processing data

        """
        base_name = os.path.splitext(source)[0]
        new_name = f"{base_name}.jp2"

        pykdu_compress.kdu_compress_cli2(infile=source, outfile=destination)
        dest = os.path.abspath(os.path.dirname(destination))
        return os.path.join(dest, new_name)


class ConvertJp2Hathi(AbsTransformation):
    """ConvertJp2Hathi."""

    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> str:
        """Transform jp2 hathi.

        Args:
            source:
            destination:
            logger: System logger. For debugging or passing processing data

        """
        dest = os.path.abspath(os.path.dirname(destination))

        base_name = os.path.splitext(os.path.basename(source))[0]
        new_name = f"{base_name}.jp2"
        new_file = os.path.join(dest, new_name)
        pykdu_compress.kdu_compress_cli2(
            infile=source,
            outfile=new_file,
            in_args=[
                "Clevels=5",
                "Clayers=8",
                "Corder=RLCP",
                "Cuse_sop=yes",
                "Cuse_eph=yes",
                "Cmodes=RESET|RESTART|CAUSAL|ERTERM|SEGMARK",
                "-no_weights",
                "-slope",
                "42988",
                "-jp2_space",
                "sRGB",
                ],
        )

        logger.info(f"Fixing up {new_file} to 400 dpi")
        set_dpi(new_file, x=400, y=400)
        return new_file


class Transformers:
    """Transformers."""

    def __init__(
            self,
            strategy: AbsTransformation,
            logger: Optional[logging.Logger] = None
    ) -> None:
        """Create a new Transformers object.

        Args:
            strategy: Strategy used to transform the packages
            logger: System logger to store information such as debug info
        """
        self._strategy = strategy
        self._logger: logging.Logger = logger or logging.getLogger(__name__)

    def transform(self, source: str, destination: str) -> None:
        """Transform one entity into another.

        Args:
            source:
            destination:

        """
        new_name = \
            self._strategy.transform(source, destination, logger=self._logger)

        path, filename = os.path.split(new_name)
        self._logger.info("Added %s in %s", filename, path)
