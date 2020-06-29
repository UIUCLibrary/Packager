import csv
import os
import sys
import tempfile
import zipfile

import pytest
import shutil
from uiucprescon import packager
from uiucprescon.packager import errors
from uiucprescon.packager.common import Metadata
from uiucprescon.packager import InstantiationTypes
from uiucprescon.packager.packages.collection_builder import \
    HathiLimitedViewBuilder
import pykdu_compress

def package_names():
    with open(os.path.join(os.path.dirname(__file__), "package_names.csv")) \
            as csvfile:
        for row in csv.reader(csvfile):
            yield row[0], True if row[1].strip() == "True" else False


@pytest.mark.parametrize("dirname,expected_valid", package_names())
def test_hathi_limited_batch_names(dirname, expected_valid):
    assert HathiLimitedViewBuilder.is_package_dir_name(dirname) \
           is expected_valid


sample_files = [
    ("dummy.txt", InstantiationTypes.SUPPLEMENTARY),
    ("dummy.TXT", InstantiationTypes.SUPPLEMENTARY),
    ("dummy.jp2", InstantiationTypes.ACCESS),
    ("dummy.JP2", InstantiationTypes.ACCESS),
    ("dummy.tif", InstantiationTypes.PRESERVATION),
    ("dummy.TIF", InstantiationTypes.PRESERVATION),
    ("dummy.exe", InstantiationTypes.UNKNOWN),
]


@pytest.mark.parametrize("sample_file,expected_valid", sample_files)
def test_get_file_type(sample_file, expected_valid):
    assert HathiLimitedViewBuilder.get_file_type(sample_file) == expected_valid
    assert True


def test_read_only_transform(capture_one_sample_package):

    capture_one_packager = packager.PackageFactory(
        packager.packages.CaptureOnePackage()
    )
    capture_one_packages = capture_one_packager.locate_packages(capture_one_sample_package)

    hathi_limited_view_packager = packager.PackageFactory(
        packager.packages.HathiLimitedView())
    with pytest.raises(NotImplementedError):
        hathi_limited_view_packager.transform(capture_one_packages, dest=".")


def test_convert(hathi_limited_view_sample_packages, monkeypatch):

    def mock_kdu_convert(infile: str, outfile: str, in_args=None, out_args=None):
        shutil.copyfile(infile, outfile)

    monkeypatch.setattr(pykdu_compress, "kdu_compress_cli2", mock_kdu_convert)
    monkeypatch.setattr(pykdu_compress, "kdu_expand_cli", mock_kdu_convert)

    digital_library_compound_builder = packager.PackageFactory(
        packager.packages.DigitalLibraryCompound())

    with tempfile.TemporaryDirectory() as tmp_dir:
        for package in hathi_limited_view_sample_packages:
            try:
                digital_library_compound_builder.transform(package, dest=tmp_dir)
            except errors.ZipFileException as e:
                print(f"{e.src} had a problem", file=sys.stderr)
                problem_file = zipfile.ZipFile(e.src)
                print(problem_file.namelist(), file=sys.stderr)
                raise


        assert len(list(os.scandir(tmp_dir))) == 1

        for i, new_package in enumerate(
                digital_library_compound_builder.locate_packages(tmp_dir)):
            assert new_package.metadata[Metadata.ID] == \
                   hathi_limited_view_sample_packages[i].metadata[Metadata.ID]

            assert new_package.metadata[Metadata.PATH] == tmp_dir





