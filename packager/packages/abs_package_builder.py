import abc
import typing
from .collection import Package


class AbsPackageBuilder(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def locate_packages(self, path) -> typing.Iterator[Package]:
        pass

    @abc.abstractmethod
    def copy(self, package, dest) -> None:
        pass
