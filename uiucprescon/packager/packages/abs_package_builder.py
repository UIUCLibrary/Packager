import abc
import logging
import typing
from .collection import Package


class AbsPackageBuilder(metaclass=abc.ABCMeta):

    log_level = logging.INFO

    @abc.abstractmethod
    def locate_packages(self, path) -> typing.Iterator[Package]:
        pass

    @abc.abstractmethod
    def transform(self, package: Package, dest: str) -> None:
        pass
