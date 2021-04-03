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
import pytest
from uiucprescon import packager
from uiucprescon.packager.packages import archival_non_eas, collection_builder


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


