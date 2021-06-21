"""Manage the collection components."""
# pylint: disable=unsubscriptable-object
import abc
import collections
import os
from tempfile import TemporaryDirectory
from typing import Optional, Union, Dict, ChainMap, Type, List, Tuple
import warnings
from zipfile import ZipFile

from uiucprescon.packager.common import Metadata, CollectionEnums
from uiucprescon.packager.common import InstantiationTypes
from uiucprescon.packager.errors import ZipFileException

MetadataTypes = Optional[Union[str, CollectionEnums]]


class AbsPackageComponent(metaclass=abc.ABCMeta):
    """Abstract base class for creating package components."""

    def __init__(self, parent: Optional['AbsPackageComponent'] = None) -> None:
        """AbsPackageComponent.

        Args:
            parent: The parent this package component belongs to
        """
        self.parent = parent
        if parent is not None:
            self.add_to_parent(child=self)

        self.component_metadata: \
            Dict[Metadata, MetadataTypes] = self.init_local_metadata()

        metadata = self._gen_combined_metadata()

        self._metadata: ChainMap[Metadata, MetadataTypes] = metadata

    @property
    def metadata(self) -> Dict[Metadata, MetadataTypes]:
        """Metadata about the component."""
        return dict(self._metadata)

    def add_to_parent(self, child) -> None:
        """Add child to parent object."""
        if self.parent is None:
            raise AttributeError("Root objects do not have parents")
        self.parent.children.append(child)

    def __len__(self) -> int:
        return len(self.children)

    def __getitem__(self, item) -> Type["AbsPackageComponent"]:
        return self.children[item]

    def __iter__(self):
        return self.children.__iter__()

    def __str__(self) -> str:
        return "{} {}".format(super().__str__(), dict(self.metadata))

    @property
    @abc.abstractmethod
    def children(self) -> List[Type["AbsPackageComponent"]]:
        """Child components of the package."""

    def _gen_combined_metadata(self) -> ChainMap[Metadata, MetadataTypes]:
        if self.parent:

            return collections.ChainMap(
                self.component_metadata,
                self.parent.metadata
            )
        return collections.ChainMap(self.component_metadata)

    @staticmethod
    def init_local_metadata() -> dict:
        """Get default metadata."""
        return dict()


class Batch(AbsPackageComponent):
    """Batch."""

    @property
    def children(self):
        return self.packages

    def __init__(
            self,
            path: Optional[str] = None,
            parent: Optional[AbsPackageComponent] = None
    ) -> None:
        """Batch.

        Args:
            path:
            parent: The parent this batch belongs to
        """
        super().__init__(parent)
        self.path = path
        self.packages: List[Package] = []


class Package(AbsPackageComponent):
    """Package."""

    def __init__(
            self,
            path: Optional[str] = None,
            parent: Optional[AbsPackageComponent] = None
    ):
        """Create a new Package object.

        Args:
            path:
            parent: The parent this package belongs to
        """
        super().__init__(parent)
        self.path = path
        self.objects: List[PackageObject] = []
        self.unidentified_objects: List[Tuple[str, str]] = []

    @property
    def children(self):
        """Child components of the package."""
        return self.objects

    @property
    def others(self):
        """Other items that are not children of the package."""
        return self.unidentified_objects


class PackageObject(AbsPackageComponent):
    """Package Object."""

    def __init__(self, parent: Optional[Package] = None) -> None:
        """PackageObject.

        Args:
             parent: The parent this package object belongs to
        """
        super().__init__(parent)
        self.package_files: List[str] = []
        self.items: List[Item] = []

    @property
    def children(self):
        """Objects's children."""
        return self.items


class Item(AbsPackageComponent):
    """Collection item."""

    def __init__(self, parent: Optional[PackageObject] = None) -> None:
        """Item.

        Args:
             parent: parent this item belongs to
        """
        super().__init__(parent)
        self.instantiations: Dict[str, Instantiation] = {}

    @property
    def children(self):
        """Item's children."""
        return self.instantiations.values()


class Instantiation(AbsPackageComponent):
    """File Instantiation."""

    def __init__(self,
                 category: InstantiationTypes = InstantiationTypes.GENERIC,
                 parent: Optional[Item] = None,
                 files=None) -> None:
        """Create a new instantiation object.

        Args:
            category: File category type
            parent: The parent this instance belongs to
        """
        self.category = category
        super().__init__(parent)
        self.component_metadata[Metadata.CATEGORY] = category
        self._files: List[str] = files or []
        self.sidecar_files: List[str] = []

    @property
    def files(self):
        """List of file names contained.

        Warnings:
            Deprecated for get_files method.

        """
        warnings.warn("Use get_files instead", DeprecationWarning)
        return self._files

    def get_files(self):
        """Make the files contained available.

        If source is a zip file, files are extracted

        Yields:
            File path to files located in instance

        """
        temp_dir = TemporaryDirectory()
        for pkg_file in self._files:
            if ".zip" in self.parent.metadata[Metadata.PATH]:
                zip_file_name = self.parent.metadata[Metadata.PATH]
                with ZipFile(zip_file_name) as zip_file:

                    # On Windows ZipFile expects unix-style slashes
                    file_to_extract = \
                        os.path.join(self.metadata[Metadata.PATH],
                                     pkg_file).replace("\\", "/")
                    try:
                        yield zip_file.extract(file_to_extract,
                                               path=temp_dir.name)

                    except KeyError as error:
                        raise ZipFileException(
                            error, zip_file=zip_file_name,
                            problem_files=[file_to_extract]
                        ) from error

            else:
                yield os.path.join(self.metadata[Metadata.PATH], pkg_file)

    @property
    def children(self):
        """Instances has no children."""
        return []

    def add_to_parent(self, child):
        """Add child to parent.

        Args:
            child:

        """
        self.parent.instantiations[self.category] = child
