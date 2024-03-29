from unittest.mock import Mock, MagicMock

import pytest

from uiucprescon.packager.packages import collection_builder
import os


def test_builder_length(monkeypatch):
    def mock_scan_dir(root):
        mock_dirs = []
        for _ in range(10):
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


@pytest.mark.filterwarnings("ignore:Use BrittleBooksBuilder")
def test_build_bb_batch(tmpdir, monkeypatch):
    def mock_scan_dir(root):
        mock_dirs = []
        for _ in range(10):
            m = MagicMock()
            m.is_dir = MagicMock(return_value=True)
            mock_dirs.append(m)
        return mock_dirs

    def mock_build_package(*args, **kwargs):
        return

    with monkeypatch.context() as mp:
        mp.setattr(os, "scandir", mock_scan_dir)
        mp.setattr(collection_builder, "build_bb_package", mock_build_package)

        x = collection_builder.build_bb_batch("./somepath")
    assert len(x) == 10

