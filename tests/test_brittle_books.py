from unittest.mock import Mock

from uiucprescon.packager.packages import collection_builder
import os


def test_builder_length(monkeypatch):
    def mock_scan_dir(root):
        mock_dirs = []
        for dir_path in range(10):
            m = Mock()
            mock_dirs.append(m)
        return mock_dirs

    def mock_build_package(*args, **kwargs):
        return
    with monkeypatch.context() as mp:
        mp.setattr(os, "scandir", mock_scan_dir)
        mp.setattr(collection_builder.BrittleBooksBuilder,
                   "build_package",
                   mock_build_package)

        builder = collection_builder.BrittleBooksBuilder()
        batch = builder.build_batch("./somepath")
    assert len(batch) == 10
