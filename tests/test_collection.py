from unittest.mock import Mock, MagicMock

import pytest

from uiucprescon.packager.packages import collection
from uiucprescon.packager import errors
from uiucprescon.packager.common import Metadata


def test_zip_error(monkeypatch):
    item = collection.Item()
    item.component_metadata[Metadata.PATH] = "somepath.zip"
    instance = collection.Instantiation(parent=item)
    instance._files = [
        "somefile.txt"
    ]
    from zipfile import ZipFile
    import io
    with monkeypatch.context() as mp:
        mp.setattr(ZipFile, "extract", Mock(side_effect=KeyError))
        mp.setattr(ZipFile, "_RealGetContents", Mock())
        mp.setattr(io, "open", MagicMock())

        with pytest.raises(errors.ZipFileException) as error:
            next(instance.get_files())

        assert error.value.src_zip_file == item.metadata[Metadata.PATH] and \
               "somefile.txt" in error.value.problem_files[0]
