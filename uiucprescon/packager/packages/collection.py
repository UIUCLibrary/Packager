import abc
import collections
import enum
import typing


class CollectionEnums(enum.Enum):
    pass


class Metadata(enum.Enum):
    ITEM_NAME = "item_name"
    ID = "id"
    PATH = "path"
    PACKAGE_TYPE = "package_type"
    CATEGORY = "category"
    TITLE_PAGE = "title_page"


class PackageTypes(CollectionEnums):
    DIGITAL_LIBRARY_COMPOUND = "Digital Library Compound Object"
    CAPTURE_ONE_SESSION = "Capture One Session Package"
    BRITTLE_BOOKS_HATHI_TRUST_SUBMISSION = "Brittle Books HathiTrust Submission Package"
    DS_HATHI_TRUST_SUBMISSION = "DS HathiTrust Submission Package"
    HATHI_TRUST_TIFF_SUBMISSION = "HathiTrust Tiff"


class InstantiationTypes(CollectionEnums):
    ACCESS = "access"
    PRESERVATION = "preservation"
    UNKNOWN = "unknown"
    GENERIC = "generic"


class AbsPackageComponent(metaclass=abc.ABCMeta):
    def __init__(self, parent=None) -> None:
        self.parent = parent
        if parent is not None:
            self.add_to_parent(child=self)

        self.component_metadata: typing.Dict[Metadata, typing.Union[str, CollectionEnums]] = self.init_local_metadata()
        metadata = self._gen_combined_metadata()
        self._metadata: typing.ChainMap[Metadata, typing.Union[str, CollectionEnums]] = metadata

    @property
    def metadata(self) -> typing.Dict[Metadata, typing.Union[str, CollectionEnums]]:
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

    def _gen_combined_metadata(self) -> typing.ChainMap[Metadata, typing.Union[str, CollectionEnums]]:
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
    def __init__(self, category: InstantiationTypes = InstantiationTypes.GENERIC,
                 parent: typing.Optional[Item] = None) -> None:
        self.category = category
        super().__init__(parent)
        self.component_metadata[Metadata.CATEGORY] = category
        self.files: typing.List[str] = []
        self.sidecar_files: typing.List[str] = []

    @property
    def children(self):
        return []

    def add_to_parent(self, child):
        self.parent.instantiations[self.category] = child
