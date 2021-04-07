# Example Archival collection/non-EAS delivered from lab:
#
# Batch (folder)
#   access (folder) (contains cropped, 400dpi, 8bit tifs)
#       00001_001-001.tif (covert to JP2 post packaging via Speedwagon)
#       00001_001-002.tif
#       00001_002-001.tif
#       00001_002-002.tif
#   preservation (folder) (contains uncropped, 600dpi, 16bit tifs)
#       00001_002-001.tif
#       00001_002-002.tif
#       00001_002-001.tif
#       00001_002-002.tif
import os
from unittest.mock import Mock

import pytest
from uiucprescon import packager
from uiucprescon.packager.packages import archival_non_eas, collection_builder, digital_library_compound


@pytest.fixture
def sample_archival_collection(tmpdir):
    batch_root = tmpdir / "batch"
    batch_root.ensure_dir()
    number_of_sample_groups = 2
    number_of_parts_each = 4
    package = []

    for group_id in range(number_of_sample_groups):
        access_path = batch_root / "access"
        access_path.ensure_dir()

        preservation_path = batch_root / "preservation"
        preservation_path.ensure_dir()

        for part_id in range(number_of_parts_each):
            file_name = f"0001_{str(group_id + 1).zfill(3)}-{str(part_id + 1).zfill(3)}.tif"

            access_file = access_path / file_name
            access_file.ensure()

            package.append(access_file)
            preservation_file = preservation_path / file_name
            preservation_file.ensure()
            package.append(preservation_file)

    return batch_root.strpath, package


class TestArchivalNonEAS:
    def test_objects(self, sample_archival_collection):
        root, files = sample_archival_collection
        factory = packager.PackageFactory(archival_non_eas.ArchivalNonEAS())
        packages = factory.locate_packages(root)
        assert len(list(packages)) == 2

    def test_items_found(self, sample_archival_collection):
        root, files = sample_archival_collection
        factory = packager.PackageFactory(archival_non_eas.ArchivalNonEAS())
        packages = list(factory.locate_packages(root))
        first_package = packages[0]
        assert len(first_package) == 4

    @pytest.fixture()
    def transformed_to_dl_compound(self, sample_archival_collection, monkeypatch):
        root, files = sample_archival_collection
        factory = packager.PackageFactory(archival_non_eas.ArchivalNonEAS())

        digital_library_format = packager.PackageFactory(
            digital_library_compound.DigitalLibraryCompound())
        import shutil
        kdu_compress_cli2 = Mock()
        copyfile = Mock()
        copy = Mock()
        output_path = os.path.join('some', 'folder')

        with monkeypatch.context() as mp:
            mp.setattr(shutil, "copyfile", copyfile)
            mp.setattr(shutil, "copy", copy)
            import pykdu_compress
            mp.setattr(pykdu_compress, "kdu_compress_cli2", kdu_compress_cli2)
            for package in list(factory.locate_packages(root)):
                digital_library_format.transform(package, output_path)
        return output_path, kdu_compress_cli2, copy

    @pytest.mark.parametrize('input_file, output_file', [
        (
                os.path.join('preservation', '0001_002-004.tif'),
                os.path.join('002', 'access', '002-004.jp2')
        ),
        (
                os.path.join('preservation', '0001_001-004.tif'),
                os.path.join('001', 'access', '001-004.jp2'),
        ),
        (
                os.path.join('preservation', '0001_002-001.tif'),
                os.path.join('002', 'access', '002-001.jp2')
        ),
    ])
    def test_transform_jp2(self,
                           sample_archival_collection,
                           transformed_to_dl_compound,
                           input_file,
                           output_file):

        root, files = sample_archival_collection
        output_path, kdu_compress_cli2, copy = transformed_to_dl_compound

        kdu_compress_cli2.assert_any_call(
            infile=os.path.join(root, input_file),
            outfile=os.path.join(output_path, output_file)
        )

    @pytest.mark.parametrize('input_file, output_file', [
        (
                os.path.join('preservation', '0001_002-004.tif'),
                os.path.join('002', 'preservation', '002-004.tif')
        ),
        (
                os.path.join('preservation', '0001_001-004.tif'),
                os.path.join('001', 'preservation', '001-004.tif'),
        ),
        (
                os.path.join('preservation', '0001_002-001.tif'),
                os.path.join('002', 'preservation', '002-001.tif')
        ),
    ])
    def test_transform_pres(self,
                           sample_archival_collection,
                           transformed_to_dl_compound,
                           input_file,
                           output_file):

        root, files = sample_archival_collection
        output_path, kdu_compress_cli2, copy = transformed_to_dl_compound
        copy.assert_any_call(
            os.path.join(root, input_file),
            os.path.join(output_path, output_file)
        )

@pytest.mark.parametrize('file_name, group, part', [
    ('0001_001-002.tif', "001", '002'),
    ('0001_001-001.tif', "001", '001'),
    ('0001_002-001.tif', "002", '001'),
    ('0001_002-002.tif', "002", '002'),
]
                         )
def test_sorter_regex(file_name, group, part):
    s = collection_builder.ArchivalNonEASBuilder()
    data = s.grouper_regex.match(file_name)
    assert data.groupdict()['group'] == group and \
           data.groupdict()['part'] == part


