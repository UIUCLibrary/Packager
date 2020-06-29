import abc
import collections
import os
import typing
import warnings
from uiucprescon.packager.common import Metadata, CollectionEnums
from uiucprescon.packager.common import InstantiationTypes
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from uiucprescon.packager.errors import ZipFileException


class AbsPackageComponent(metaclass=abc.ABCMeta):
    def __init__(self, parent=None) -> None:
        self.parent = parent
        if parent is not None:
            self.add_to_parent(child=self)

        self.component_metadata: \
            typing.Dict[Metadata, typing.Union[str, CollectionEnums]] = \
            self.init_local_metadata()

        metadata = self._gen_combined_metadata()

        self._metadata: \
            typing.ChainMap[Metadata,
                            typing.Union[str, CollectionEnums]] = metadata

    @property
    def metadata(self) -> \
            typing.Dict[Metadata, typing.Union[str, CollectionEnums]]:

        return dict(self._metadata)

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

    def _gen_combined_metadata(self) -> \
            typing.ChainMap[Metadata, typing.Union[str, CollectionEnums]]:

        if self.parent:

            metadata = collections.ChainMap(self.component_metadata,
                                            self.parent.metadata)
        else:
            metadata = collections.ChainMap(self.component_metadata)
        return metadata

    @staticmethod
    def init_local_metadata() -> dict:
        return dict()


class Batch(AbsPackageComponent):
    @property
    def children(self):
        return self.packages

    def __init__(self, path=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.packages:  typing.List[Package] = []


class Package(AbsPackageComponent):
    def __init__(self, path=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.objects: typing.List[PackageObject] = []
        self.unidentified_objects: typing.List[typing.Tuple[str, str]] = []

    @property
    def children(self):
        return self.objects

    @property
    def others(self):
        return self.unidentified_objects


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
    def __init__(self,
                 category: InstantiationTypes = InstantiationTypes.GENERIC,
                 parent: typing.Optional[Item] = None) -> None:

        self.category = category
        super().__init__(parent)
        self.component_metadata[Metadata.CATEGORY] = category
        self._files: typing.List[str] = []
        self.sidecar_files: typing.List[str] = []

    @property
    def files(self):
        warnings.warn("Use get_files instead", DeprecationWarning)
        return self._files

    def get_files(self):
        temp_dir = TemporaryDirectory()
        for f in self._files:
            if ".zip" in self.parent.metadata[Metadata.PATH]:
                zip_file_name = self.parent.metadata[Metadata.PATH]
                with ZipFile(zip_file_name) as zip_file:
                    temp_file = os.path.join(temp_dir.name,
                                             self.metadata[Metadata.PATH],
                                             f)

                    file_to_extract = os.path.normcase(os.path.join(self.metadata[Metadata.PATH], f))
                    try:
                        zip_file.extract(file_to_extract, path=temp_dir.name)
                    except KeyError as e:
                        raise ZipFileException(e, zip_file=zip_file_name,
                                               problem_files=[file_to_extract])
                    yield temp_file
            else:
                yield os.path.join(self.metadata[Metadata.PATH], f)

    @property
    def children(self):
        return []

    def add_to_parent(self, child):
        self.parent.instantiations[self.category] = child
