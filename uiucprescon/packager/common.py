"""Shared utility functions."""

import enum


class CollectionEnums(enum.Enum):
    """CollectionEnums."""


class Metadata(enum.Enum):
    """Metadata."""

    ITEM_NAME = "item_name"
    ID = "id"
    PATH = "path"
    PACKAGE_TYPE = "package_type"
    CATEGORY = "category"
    TITLE_PAGE = "title_page"


class PackageTypes(CollectionEnums):
    """PackageTypes."""

    DIGITAL_LIBRARY_COMPOUND = "Digital Library Compound Object"
    CAPTURE_ONE_SESSION = "Capture One Session Package"

    BRITTLE_BOOKS_HATHI_TRUST_SUBMISSION = \
        "Brittle Books HathiTrust Submission Package"

    DS_HATHI_TRUST_SUBMISSION = "DS HathiTrust Submission Package"
    HATHI_TRUST_TIFF_SUBMISSION = "HathiTrust Tiff"
    HATHI_TRUST_JP2_SUBMISSION = "HathiTrust Jpeg 2000"


class InstantiationTypes(CollectionEnums):
    """InstantiationTypes."""

    ACCESS = "access"
    PRESERVATION = "preservation"
    UNKNOWN = "unknown"
    GENERIC = "generic"
    SUPPLEMENTARY = "supplementary"
