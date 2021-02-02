import os
import shutil
import sys

from uiucprescon import packager
from uiucprescon.packager import Metadata
from uiucprescon.packager.packages import collection_builder, collection
import pytest
import pykdu_compress

CAPTURE_ONE_BATCH_NAME = "capture_one_batch"
DESTINATION_NAME = "out"


@pytest.fixture(scope="session")
def capture_one_fixture(tmpdir_factory):
    test_dir = tmpdir_factory.mktemp("test", numbered=False)

    os.makedirs(os.path.join(test_dir, CAPTURE_ONE_BATCH_NAME))
    os.makedirs(os.path.join(test_dir, DESTINATION_NAME))
    # Create a bunch of empty files that represent a capture one batch session

    with open(os.path.join(
            test_dir, CAPTURE_ONE_BATCH_NAME, "000001_00000001.tif"), "w"):
        pass

    with open(os.path.join(
            test_dir, CAPTURE_ONE_BATCH_NAME, "000001_00000002.tif"), "w"):
        pass

    with open(os.path.join(
            test_dir, CAPTURE_ONE_BATCH_NAME, "000001_00000003.tif"), "w"):
        pass

    with open(os.path.join(
            test_dir, CAPTURE_ONE_BATCH_NAME, "000002_00000001.tif"), "w"):
        pass

    with open(os.path.join(
            test_dir, CAPTURE_ONE_BATCH_NAME, "000002_00000002.tif"), "w"):
        pass

    yield test_dir
    shutil.rmtree(test_dir)


def test_capture_one_tiff_to_hathi_tiff(capture_one_fixture):
    source = os.path.join(capture_one_fixture, CAPTURE_ONE_BATCH_NAME)
    dest = os.path.join(capture_one_fixture, DESTINATION_NAME)

    capture_one_packages_factory = packager.PackageFactory(
        packager.packages.CaptureOnePackage(delimiter="_"))

    # find all Capture One organized packages
    capture_one_packages = \
        list(capture_one_packages_factory.locate_packages(path=source))

    # There should be 2 packages in this sample batch
    assert len(capture_one_packages) == 2

    hathi_tiff_package_factory = \
        packager.PackageFactory(packager.packages.HathiTiff())

    for capture_one_package in capture_one_packages:
        hathi_tiff_package_factory.transform(capture_one_package, dest=dest)

    # This should result in the following files
    #
    # some_root/000001/00000001.tif
    # some_root/000001/00000002.tif
    # some_root/000001/00000003.tif
    assert os.path.exists(os.path.join(dest, "000001", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000002.tif"))
    assert os.path.exists(os.path.join(dest, "000001", "00000003.tif"))

    # some_root/000002/00000001.tif
    # some_root/000002/00000002.tif
    assert os.path.exists(os.path.join(dest, "000002", "00000001.tif"))
    assert os.path.exists(os.path.join(dest, "000002", "00000002.tif"))


def test_capture_one_tiff_package_size(capture_one_fixture):
    source = os.path.join(capture_one_fixture, CAPTURE_ONE_BATCH_NAME)

    capture_one_packages_factory = \
        packager.PackageFactory(packager.packages.CaptureOnePackage())

    # find all Capture One organized packages
    capture_one_packages = \
        list(capture_one_packages_factory.locate_packages(path=source))

    # There should be 2 packages in this sample batch
    assert len(capture_one_packages) == 2


def test_capture_one_tiff_to_digital_library(capture_one_fixture, monkeypatch):

    def dummy_kdu_command(args):
        split_args = args.split()
        output_arg = os.path.abspath(split_args[3].strip('"'))
        with open(output_arg, "w") as f:
            pass
        pass

    def dummy_kdu_compress_cli2(infile, outfile, in_args=None, out_args=None):
        with open(outfile, "w") as f:
            pass
        pass

    monkeypatch.setattr(pykdu_compress, 'kdu_compress_cli', dummy_kdu_command)
    monkeypatch.setattr(pykdu_compress, 'kdu_compress_cli2', dummy_kdu_compress_cli2)

    source = os.path.join(capture_one_fixture, CAPTURE_ONE_BATCH_NAME)
    dest = os.path.join(capture_one_fixture, DESTINATION_NAME)

    capture_one_packages_factory = packager.PackageFactory(
        packager.packages.CaptureOnePackage())

    # find all Capture One organized packages

    capture_one_packages = \
        list(capture_one_packages_factory.locate_packages(path=source))

    # There should be 2 packages in this sample batch
    assert len(capture_one_packages) == 2

    dl_factory = packager.PackageFactory(
        packager.packages.DigitalLibraryCompound())

    for capture_one_package in capture_one_packages:
        dl_factory.transform(capture_one_package, dest=dest)

    # This should result in the following files
    #
    #  some_root/000001/preservation/00000001.tif
    assert os.path.exists(
        os.path.join(dest, "000001", 'preservation', "000001_00000001.tif"))

    #  some_root/000001/access/
    assert os.path.exists(
        os.path.join(dest, "000001", 'access', "000001_00000001.jp2"))

    #  some_root/000001/preservation/00000002.tif
    assert os.path.exists(
        os.path.join(dest, "000001", 'preservation', "000001_00000002.tif"))
    #  some_root/000001/access/
    assert os.path.exists(
        os.path.join(dest, "000001", 'access', "000001_00000002.jp2"))

    #  some_root/000001/preservation/00000003.tif
    assert os.path.exists(
        os.path.join(dest, "000001", 'preservation', "000001_00000003.tif"))
    #  some_root/000001/access/
    assert os.path.exists(
        os.path.join(dest, "000001", 'access', "000001_00000003.jp2"))

    #  some_root/000002/preservation/00000001.tif
    assert os.path.exists(
        os.path.join(dest, "000002", "preservation", "000002_00000001.tif"))
    #  some_root/000002/access/
    assert os.path.exists(
        os.path.join(dest, "000002", "access", "000002_00000001.jp2"))

    #  some_root/000002/preservation/00000001.tif
    assert os.path.exists(
        os.path.join(dest, "000002", "preservation", "000002_00000001.tif"))

    #  some_root/000002/access/
    assert os.path.exists(
        os.path.join(dest, "000002", "access"))


@pytest.fixture(scope="session")
def capture_one_batch_with_dashes(tmpdir_factory):
    base_level = tmpdir_factory.mktemp("package")
    included_files = [
        f"99423682912205899-{str(x).zfill(8)}.tif" for x in range(20)
    ]

    for dummy_file in included_files:
        (base_level / dummy_file).ensure()

    yield base_level.strpath, included_files

    base_level.remove()


def test_capture_one_dashes(capture_one_batch_with_dashes):
    batch_dir, source_files = capture_one_batch_with_dashes

    capture_one_packages_factory = packager.PackageFactory(
        packager.packages.CaptureOnePackage(delimiter="-"))

    res = next(capture_one_packages_factory.locate_packages(batch_dir))
    assert len(res) == len(source_files)


def test_builder2_build_batch_has_path(capture_one_batch_with_dashes):
    batch_dir, source_files = capture_one_batch_with_dashes
    builder = collection_builder.CaptureOneBuilder()
    builder.splitter = collection_builder.dash_splitter
    batch = builder.build_batch(batch_dir)
    assert batch.path == batch_dir


def test_builder2_build_package_files_match(capture_one_batch_with_dashes):
    batch_dir, source_files = capture_one_batch_with_dashes
    builder = collection_builder.CaptureOneBuilder()
    builder.splitter = collection_builder.dash_splitter
    sample_object = collection.PackageObject()
    sample_object.component_metadata[Metadata.ID] = "99423682912205899"
    builder.build_package(sample_object, batch_dir)
    assert len(sample_object) == len(source_files)


def test_builder2_build_instance(capture_one_batch_with_dashes):
    batch_dir, source_files = capture_one_batch_with_dashes
    builder = collection_builder.CaptureOneBuilder()
    builder.splitter = collection_builder.dash_splitter
    sample_item = collection.Item()
    sample_item.component_metadata[Metadata.ID] = "00001"
    builder.build_instance(parent=sample_item, path=batch_dir, filename=source_files[0])
    assert len(sample_item) == 1


sample_underscore_file_names = [
    ('000001_00000001.tif', True, "000001", "00000001"),
    ('000001_00000001.jp2', True, "000001", "00000001"),
    ('000001-00000001.tif', False, None, None),
    ('000001-00000001.jp2', False, None, None),
    ('asdfsadfasdf.tif', False, None, None),
]


@pytest.mark.parametrize("file_path, is_valid, expected_group, expected_item", sample_underscore_file_names)
def test_underscore_splitter(file_path, is_valid, expected_group, expected_item):
    result = collection_builder.underscore_splitter(file_path)
    if result is None:
        assert is_valid is False
        return
    assert result['group'] == expected_group and result['part'] == expected_item


@pytest.mark.parametrize("file_path, is_valid, expected_group, expected_item", sample_underscore_file_names)
def test_splitter(file_path, is_valid, expected_group, expected_item):
    builder = collection_builder.CaptureOneBuilder()
    result = builder.identify_file_name_parts(file_path)
    if result is None:
        assert is_valid is False
        return
    assert result['group'] == expected_group and result['part'] == expected_item


sample_dashed_file_names = [
    ('000001_00000001.tif', False, None, None),
    ('000001_00000001.jp2', False, None, None),
    ('000001-00000001.tif', True, "000001", "00000001"),
    ('000001-00000001.jp2', False, "000001", '00000001'),
    ('asdfsadfasdf.tif', False, None, None),
]
@pytest.mark.parametrize("file_path, is_valid, expected_group, expected_item", sample_dashed_file_names)
def test_splitter_dashed(file_path, is_valid, expected_group, expected_item):
    builder = collection_builder.CaptureOneBuilder()
    builder.splitter = collection_builder.dash_splitter
    result = builder.identify_file_name_parts(file_path)
    if result is None:
        assert is_valid is False
        return
    assert result['group'] == expected_group and result['part'] == expected_item
