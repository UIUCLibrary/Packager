import abc
import typing
from collections import namedtuple

PackageItem = namedtuple("PackageItem", ["root", "identifier", "directories"])


class AbsPackage(metaclass=abc.ABCMeta):
    def __init__(self, root_path=None):
        self.root_path = root_path

    def __len__(self):
        return len(list(self.get_packages(self.root_path)))

    def __iter__(self):
        for i in self.get_packages(self.root_path):
            yield i

    @staticmethod
    @abc.abstractmethod
    def get_packages(path) -> typing.Iterable[PackageItem]:
        pass
