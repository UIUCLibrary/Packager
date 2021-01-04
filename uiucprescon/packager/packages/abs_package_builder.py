"""Abstract class for package builder."""
import abc
import logging
import typing
from .collection import Package


class AbsPackageBuilder(metaclass=abc.ABCMeta):
    """Base class for working with file packages."""

    log_level = logging.INFO

    @abc.abstractmethod
    def locate_packages(self, path) -> typing.Iterator[Package]:
        """Locate packages found at a given path."""

    @abc.abstractmethod
    def transform(self, package: Package, dest: str) -> None:
        """Transform a package into a the current type at given destination."""
