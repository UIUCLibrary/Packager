import abc
import logging
import os
import shutil

try:
    import pykdu_compress
except ImportError as e:
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
        dest = os.path.abspath(os.path.dirname(destination))

        pykdu_compress.kdu_compress_cli("-i \"{}\" -o \"{}\"".format(source,
                                                             destination))
        logger.info("Generated {} in {}".format(source_name, dest))


class ConvertJp2Hathi(AbsTransformation):

    def transform(self, source: str, destination: str,
                  logger: logging.Logger) -> None:

        source_name = os.path.basename(source)

        dest = os.path.abspath(os.path.dirname(destination))

        pykdu_compress.kdu_compress_cli(
            "-i \"{}\" "
            "Clevels=5 "
            "Clayers=8 "
            "Corder=RLCP "
            "Cuse_sop=yes "
            "Cuse_eph=yes "
            "Cmodes=RESET|RESTART|CAUSAL|ERTERM|SEGMARK "
            "-no_weights "
            "-slope 42988 "
            "-jp2_space sRGB "
            "-o \"{}\"".format(source, destination))

        logger.info("Generated {} in {}".format(source_name, dest))


class Transformers:
    def __init__(self, strategy: AbsTransformation,
                 logger: logging.Logger = None) -> None:
        self._strategy = strategy
        self._logger: logging.Logger = logger or logging.getLogger(__name__)

    def transform(self, source, destination) -> None:
        return self._strategy.transform(source, destination,
                                        logger=self._logger)
