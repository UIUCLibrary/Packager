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
    import pathlib

    def kdu_compress_cli2(infile: str,
                          outfile: str, in_args=None, out_args=None):
        pathlib.Path(outfile).touch()

    def kdu_expand_cli(infile: str, outfile: str, in_args=None, out_args=None):
        pathlib.Path(outfile).touch()

    monkeypatch.setattr(pykdu_compress, "kdu_compress_cli2", kdu_compress_cli2)
    monkeypatch.setattr(pykdu_compress, "kdu_expand_cli", kdu_expand_cli)

    digital_library_compound_builder = packager.PackageFactory(
        packager.packages.DigitalLibraryCompound())

    with tempfile.TemporaryDirectory() as tmp_dir:
        for package in hathi_limited_view_sample_packages:
            try:
                digital_library_compound_builder.transform(package,
                                                           dest=tmp_dir)

            except errors.ZipFileException as e:

                print(f"{e.src_zip_file} had a problem", file=sys.stderr)

                if len(e.problem_files) > 0:
                    print(f"Problems with {','.join(e.problem_files)}",
                          file=sys.stderr)

                problem_file = zipfile.ZipFile(e.src_zip_file)
                print(problem_file.namelist(), file=sys.stderr)
                raise
        assert len(list(os.scandir(tmp_dir))) == 1

        for i, new_package in enumerate(
                digital_library_compound_builder.locate_packages(tmp_dir)):
            assert new_package.metadata[Metadata.ID] == \
                   hathi_limited_view_sample_packages[i].metadata[Metadata.ID]

            sample_item = new_package.items[0]
            access = sample_item.instantiations[InstantiationTypes.ACCESS]
            access_files = list(access.get_files())
            assert len(access_files) > 0

            pres = sample_item.instantiations[InstantiationTypes.PRESERVATION]
            pres_files = list(pres.get_files())
            assert len(pres_files) > 0
            assert new_package.metadata[Metadata.PATH] == tmp_dir




