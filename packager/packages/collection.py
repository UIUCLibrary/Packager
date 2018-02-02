import abc
import collections
import typing


class AbsPackageComponent(metaclass=abc.ABCMeta):
    def __init__(self, parent=None) -> None:
        self.parent = parent
        if parent is not None:
            self.add_to_parent(child=self)

        self.component_metadata = self.init_local_metadata()
        metadata = self._gen_combined_metadata()
        self.metadata: typing.ChainMap[str, str] = metadata

    def add_to_parent(self, child):
        self.parent.children.append(child)

    def __len__(self):
        return len(self.children)

    def __getitem__(self, item) -> typing.Type["AbsPackageComponent"]:
        return self.children[item]

    def __iter__(self):
        return self.children.__iter__()

    def __str__(self) -> str:
        return "{} {}".format(super().__str__(), dict(self.metadata))

    @property
    @abc.abstractmethod
    def children(self) -> typing.List[typing.Type["AbsPackageComponent"]]:
        pass

    def _gen_combined_metadata(self) -> typing.ChainMap[str, str]:
        if self.parent:
            metadata = collections.ChainMap(self.component_metadata, self.parent.metadata)
        else:
            metadata = collections.ChainMap(self.component_metadata)
        return metadata

    @staticmethod
    def init_local_metadata() -> dict:
        return dict()


class Package(AbsPackageComponent):
    def __init__(self, path=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.objects: typing.List[PackageObject] = []

    @property
    def children(self):
        return self.objects


class PackageObject(AbsPackageComponent):
    def __init__(self, parent: typing.Optional[Package] = None) -> None:
        super().__init__(parent)
        self.package_files: typing.List[str] = []
        self.items: typing.List[Item] = []

    @property
    def children(self):
        return self.items


class Item(AbsPackageComponent):
    def __init__(self, parent: typing.Optional[PackageObject] = None) -> None:
        super().__init__(parent)
        self.instantiations = dict()  # type: typing.Dict[str, Instantiation]

    @property
    def children(self):
        return self.instantiations.values()


class Instantiation(AbsPackageComponent):
    def __init__(self, category="generic", parent: typing.Optional[Item] = None) -> None:
        self.category = category
        super().__init__(parent)
        self.component_metadata['category'] = category
        self.files: typing.List[str] = []

    @property
    def children(self):
        return []

    def add_to_parent(self, child):
        self.parent.instantiations[self.category] = child
