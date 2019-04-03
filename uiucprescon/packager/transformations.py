import abc
import logging
import os
import shutil
from py3exiv2bind.core import set_dpi
try:
    import pykdu_compress
except ImportError:
    print("Unable to use transform DigitalLibraryCompound due to "
          "missing import")


class AbsTransformation(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> None:
        pass


class CopyFile(AbsTransformation):
    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> None:

        dest = os.path.abspath(os.path.dirname(destination))
        source_name = os.path.basename(source)

        logger.debug("Copying {} to {}".format(source_name, dest))
        shutil.copy(source, destination)
        logger.info("Added {} to {}".format(source_name, dest))


class ConvertJp2Standard(AbsTransformation):

    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> None:

        source_name = os.path.basename(source)
        base_name, ext = os.path.splitext(source)
        new_name = f"{base_name}.jp2"
        dest = os.path.abspath(os.path.dirname(destination))

        pykdu_compress.kdu_compress_cli2(infile=source, outfile=destination)

        logger.info("Generated {} in {}".format(new_name, dest))


class ConvertJp2Hathi(AbsTransformation):

    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> None:
        dest = os.path.abspath(os.path.dirname(destination))

        # new_name = destination.replace(".tif", ".jp2")
        base_name, ext = os.path.splitext(os.path.basename(source))
        new_name = f"{base_name}.jp2"
        pykdu_compress.kdu_compress_cli2(
            infile=source,
            outfile=new_name,
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

        logger.info("Fixing up image to 400 dpi")
        set_dpi(new_name, x=400, y=400)

        logger.info("Generated {} in {}".format(
            os.path.basename(new_name), dest))


class Transformers:
    def __init__(self, strategy: AbsTransformation,
                 logger: logging.Logger = None) -> None:
        self._strategy = strategy
        self._logger: logging.Logger = logger or logging.getLogger(__name__)

    def transform(self, source, destination) -> None:
        return self._strategy.transform(source, destination,
                                        logger=self._logger)
