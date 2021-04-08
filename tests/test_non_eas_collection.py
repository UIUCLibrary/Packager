import os
from unittest.mock import Mock
import typing
import pytest
from uiucprescon import packager
from uiucprescon.packager.packages import \
    noneas, digital_library_compound

# Example Archival collection/non-EAS delivered from lab:
#
# Batch (folder)
#   access (folder) (contains cropped, 400dpi, 8bit tifs)
#       00001_001-001.tif
#       00001_001-002.tif
#       00001_002-001.tif
#       00001_002-002.tif
#   preservation (folder)
#       00001_002-001.tif
#       00001_002-002.tif
#       00001_002-001.tif
#       00001_002-002.tif


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
            file_name = \
                f"0001_{str(group_id + 1).zfill(3)}-{str(part_id + 1).zfill(3)}.tif"

            access_file = access_path / file_name
            access_file.ensure()

            package.append(access_file.strpath)
            preservation_file = preservation_path / file_name
            preservation_file.ensure()
            package.append(preservation_file.strpath)

    return batch_root.strpath, package


class TestArchivalNonEAS:
    def test_objects(self, sample_archival_collection):
        root, files = sample_archival_collection
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        packages = factory.locate_packages(root)
        assert len(list(packages)) == 2

    def test_items_found(self, sample_archival_collection):
        root, files = sample_archival_collection
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        packages = list(factory.locate_packages(root))
        first_package = packages[0]
        assert len(first_package) == 4


class TestArchivalTransformToDigitalLibraryCompound:

    @pytest.fixture()
    def transformed_to_dl_compound(self, sample_archival_collection, monkeypatch):
        root, files = sample_archival_collection
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())

        digital_library_format = packager.PackageFactory(
            digital_library_compound.DigitalLibraryCompound())
        import shutil
        kdu_compress_cli2 = Mock()
        output_path = os.path.join('some', 'folder')
        transform = Mock()
        with monkeypatch.context() as mp:
            mp.setattr(
                packager.transformations.Transformers, "transform", transform
            )
            mp.setattr(shutil, "copyfile", Mock())
            mp.setattr(shutil, "copy", Mock())
            import pykdu_compress
            mp.setattr(pykdu_compress, "kdu_compress_cli2", kdu_compress_cli2)
            for package in list(factory.locate_packages(root)):
                digital_library_format.transform(package, output_path)
        return output_path, transform

    @pytest.mark.parametrize('input_file, output_file', [
        (
                os.path.join('access', '0001_002-004.tif'),
                os.path.join('002', 'access', '002-004.jp2')
        ),
        (
                os.path.join('access', '0001_001-004.tif'),
                os.path.join('001', 'access', '001-004.jp2'),
        ),
        (
                os.path.join('access', '0001_002-001.tif'),
                os.path.join('002', 'access', '002-001.jp2')
        ),

    ])
    def test_transform_jp2(self,
                           sample_archival_collection,
                           transformed_to_dl_compound,
                           input_file,
                           output_file):

        root, _ = sample_archival_collection
        output_path, transform = transformed_to_dl_compound
        assert transform.called is True
        expected_source = os.path.join(root, input_file)
        expected_destination = os.path.join(output_path, output_file)
        transform.assert_any_call(expected_source, expected_destination)

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
    def test_transform_pres(
            self,
            sample_archival_collection,
            transformed_to_dl_compound,
            input_file,
            output_file
    ):

        root, files = sample_archival_collection
        output_path, transform = transformed_to_dl_compound
        assert transform.called is True
        transform.assert_any_call(
            source=os.path.join(root, input_file),
            destination=os.path.join(output_path, output_file)
        )


@pytest.mark.parametrize('file_name, group, part', [
    ('0001_001-002.tif', "001", '002'),
    ('0001_001-001.tif', "001", '001'),
    ('0001_002-001.tif', "002", '001'),
    ('0001_002-002.tif', "002", '002'),
]
                         )
def test_sorter_regex(file_name, group, part):
    s = noneas.ArchivalNonEASBuilder()
    data = s.grouper_regex.match(file_name)
    assert data.groupdict()['group'] == group and \
           data.groupdict()['part'] == part


# Example Cataloged collection/non-EAS delivered from lab:
#
# Batch (folder)
#     access (folder) (contains cropped, 400dpi, 8bit tifs)
#         MMSID1-001.tif
#         MMSID1-002.tif
#         MMSID2-001.tif
#         MMSID2-002.tif
#
#     preservation (folder) (contains uncropped, 600dpi, 16bit tifs)
#         MMSID1-001.tif
#         MMSID1-002.tif
#         MMSID2-001.tif
#         MMSID2-002.tif


@pytest.fixture
def sample_cataloged_collection(monkeypatch) -> typing.Tuple[str, typing.List[str]]:
    batch_root = os.path.join("dummy", "batch")
    number_of_sample_groups = 2
    number_of_parts_each = 4
    packages: typing.Set[str] = set()

    def scandir(path):
        if path == batch_root:
            for f in packages:
                mock_item = Mock(path=f)
                mock_item.name = os.path.split(f)[-1]
                if f.endswith(".tif"):
                   mock_item.is_file = Mock(return_value=True)
                   mock_item.is_dir = Mock(return_value=False)
                else:
                   mock_item.is_file = Mock(return_value=False)
                   mock_item.is_dir = Mock(return_value=True)
                yield mock_item
        elif path == os.path.join(batch_root, "access"):
            for f in packages:
                if "access" not in f:
                    continue

                mock_item = Mock(path=f)
                mock_item.name = os.path.split(f)[-1]
                if f.endswith(".tif"):
                    mock_item.is_file = Mock(return_value=True)
                    mock_item.is_dir = Mock(return_value=False)
                else:
                    mock_item.is_file = Mock(return_value=False)
                    mock_item.is_dir = Mock(return_value=True)
                yield mock_item
        elif path == os.path.join(batch_root, "preservation"):
            for f in packages:
                if "preservation" not in f:
                    continue

                mock_item = Mock(path=f)
                mock_item.name = os.path.split(f)[-1]
                if f.endswith(".tif"):
                    mock_item.is_file = Mock(return_value=True)
                    mock_item.is_dir = Mock(return_value=False)
                else:
                    mock_item.is_file = Mock(return_value=False)
                    mock_item.is_dir = Mock(return_value=True)
                yield mock_item

    monkeypatch.setattr(os, 'scandir', scandir)
    for group_id in range(number_of_sample_groups):
        access_path = os.path.join(batch_root, "access")

        preservation_path = os.path.join(batch_root, "preservation")
        for part_id in range(number_of_parts_each):
            file_name = \
                f"991001{str(group_id + 1)}205899-{str(part_id + 1).zfill(3)}.tif"

            access_file = os.path.join(access_path, file_name)

            packages.add(access_file)
            preservation_file = os.path.join(preservation_path, file_name)
            packages.add(preservation_file)

    return batch_root, list(packages)


class TestCatalogedNonEAS:
    def test_objects(self, sample_cataloged_collection):
        root, files = sample_cataloged_collection
        factory = packager.PackageFactory(noneas.CatalogedNonEAS())
        packages = factory.locate_packages(root)
        assert len(list(packages)) == 2

    def test_items_found(self, sample_cataloged_collection):
        root, files = sample_cataloged_collection
        factory = packager.PackageFactory(noneas.CatalogedNonEAS())
        packages = list(factory.locate_packages(root))
        first_package = packages[0]
        assert len(first_package) == 4


class TestCatalogedTransformToDigitalLibraryCompound:

    @pytest.fixture()
    def transformed_to_dl_compound(
            self, sample_cataloged_collection, monkeypatch):

        root, files = sample_cataloged_collection
        factory = packager.PackageFactory(noneas.CatalogedNonEAS())
        digital_library_format = packager.PackageFactory(
            digital_library_compound.DigitalLibraryCompound())
        output_path = os.path.join('some', 'folder')
        transform = Mock()

        def mock_transform(_, source, destination):
            transform(source=source, destination=destination)

        with monkeypatch.context() as mp:
            mp.setattr(
                packager.transformations.Transformers,
                "transform", mock_transform
            )
            for package in list(factory.locate_packages(root)):
                digital_library_format.transform(package, output_path)

        return output_path, transform

    @pytest.mark.parametrize('input_file, output_file', [
        (
            os.path.join('dummy', 'batch',
                         'access', '9910011205899-002.tif'),
            os.path.join('9910011205899',
                         'access', '9910011205899-002.jp2')
        ),
        (
            os.path.join('dummy', 'batch',
                         'access', '9910011205899-001.tif'),
            os.path.join('9910011205899',
                         'access', '9910011205899-001.jp2'),
        ),
        (
            os.path.join('dummy', 'batch',
                         'access', '9910012205899-001.tif'),
            os.path.join('9910012205899',
                         'access', '9910012205899-001.jp2'),
        ),
        (
            os.path.join('dummy', 'batch',
                         'preservation', '9910011205899-002.tif'),
            os.path.join('9910011205899',
                         'preservation', '9910011205899-002.tif')
        ),
        (
            os.path.join('dummy', 'batch',
                         'preservation', '9910011205899-001.tif'),
            os.path.join('9910011205899',
                         'preservation', '9910011205899-001.tif'),
        ),
        (
            os.path.join('dummy', 'batch',
                         'preservation', '9910012205899-001.tif'),
            os.path.join('9910012205899',
                         'preservation',  '9910012205899-001.tif'),
        ),
    ])
    def test_transform(
            self, transformed_to_dl_compound, input_file, output_file):

        output_path, transform = transformed_to_dl_compound
        assert transform.called is True
        expected_destination = os.path.join(output_path, output_file)
        transform.assert_any_call(source=input_file,
                                  destination=expected_destination)
