import abc


class AbsPackageFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create(self, package_name):
        pass