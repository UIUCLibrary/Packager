import os
from unittest.mock import Mock, ANY, call
import typing
import pytest

import uiucprescon.packager.transformations
from uiucprescon import packager
from uiucprescon.packager.packages import \
    noneas, digital_library_compound, hathi_jp2_package


class TestArchivalNonEAS:

    @pytest.fixture
    def sample_collection(self, tmpdir):
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
                    f"0001_{str(group_id + 1).zfill(3)}" \
                    f"-" \
                    f"{str(part_id + 1).zfill(3)}.tif"

                access_file = access_path / file_name
                access_file.ensure()

                package.append(access_file.strpath)
                preservation_file = preservation_path / file_name
                preservation_file.ensure()
                package.append(preservation_file.strpath)

        yield batch_root.strpath, package
        tmpdir.remove()

    @pytest.fixture()
    def sample_collection_longer(self, tmpdir):
        # Example Archival collection/non-EAS delivered from lab:
        #
        # Batch (folder)
        #   access (folder) (contains cropped, 400dpi, 8bit tifs)
        #       0333_003_003_01-001.tif
        #       0333_003_003_01-002.tif
        #       0333_003_003_01-003.tif
        #       0333_003_003_01-004.tif
        #       0333_003_003_02-001.tif
        #       0333_003_003_02-002.tif
        #       0333_003_003_02-003.tif
        #       0333_003_003_02-004.tif
        #   preservation (folder)
        #       0333_003_003_01-001.tif
        #       0333_003_003_01-002.tif
        #       0333_003_003_01-003.tif
        #       0333_003_003_01-004.tif
        #       0333_003_003_02-001.tif
        #       0333_003_003_02-002.tif
        #       0333_003_003_02-003.tif
        #       0333_003_003_02-004.tif

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
                    f"0333_003_003_0{str(group_id + 1)}" \
                    f"-" \
                    f"{str(part_id + 1).zfill(3)}.tif"

                access_file = access_path / file_name
                access_file.ensure()

                package.append(access_file.strpath)
                preservation_file = preservation_path / file_name
                preservation_file.ensure()
                package.append(preservation_file.strpath)

        yield batch_root.strpath, package
        tmpdir.remove()

    def test_objects(self, sample_collection):
        root, files = sample_collection
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        packages = factory.locate_packages(root)
        assert len(list(packages)) == 2

    def test_items_found(self, sample_collection):
        root, files = sample_collection
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        packages = list(factory.locate_packages(root))
        first_package = packages[0]
        assert len(first_package) == 4

    def test_objects_longer(self, sample_collection_longer):
        root, files = sample_collection_longer
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        packages = factory.locate_packages(root)
        assert len(list(packages)) == 2

    def test_items_found_longer(self, sample_collection_longer):
        root, files = sample_collection_longer
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        packages = list(factory.locate_packages(root))
        first_package = packages[0]
        assert len(first_package) == 4

    @pytest.fixture()
    def transformed_to_dl_compound(
            self, sample_collection, monkeypatch
    ):

        root, files = sample_collection
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
            mp.setattr(
                uiucprescon.packager.transformations.CopyFile,
                "transform",
                transform
            )
            mp.setattr(
                uiucprescon.packager.transformations.ConvertJp2Standard,
                "transform",
                transform
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
                os.path.join('0001_002', 'access', '0001_002-004.jp2')
        ),
        (
                os.path.join('access', '0001_001-004.tif'),
                os.path.join('0001_001', 'access', '0001_001-004.jp2'),
        ),
        (
                os.path.join('access', '0001_002-001.tif'),
                os.path.join('0001_002', 'access', '0001_002-001.jp2')
        ),

    ])
    def test_transform_dl_compound_jp2(
            self,
            sample_collection,
            transformed_to_dl_compound,
            input_file,
            output_file
    ):

        root, _ = sample_collection
        output_path, transform = transformed_to_dl_compound
        assert transform.called is True
        expected_source = os.path.join(root, input_file)
        expected_destination = os.path.join(output_path, output_file)

        assert \
            call(expected_source, expected_destination, ANY) in \
            transform.call_args_list, \
            f"Expected {expected_source} source, " \
            f"got {[x.args[0] for x in transform.call_args_list]}"

    @pytest.mark.parametrize('input_file, output_file', [
        (
                os.path.join('preservation', '0001_002-004.tif'),
                os.path.join('0001_002', 'preservation', '0001_002-004.tif')
        ),
        (
                os.path.join('preservation', '0001_001-004.tif'),
                os.path.join('0001_001', 'preservation', '0001_001-004.tif'),
        ),
        (
                os.path.join('preservation', '0001_001-001.tif'),
                os.path.join('0001_001', 'preservation', '0001_001-001.tif'),
        ),
        (
                os.path.join('preservation', '0001_002-001.tif'),
                os.path.join('0001_002', 'preservation', '0001_002-001.tif')
        ),
    ])
    def test_transform_to_dl_compound_pres(
            self,
            sample_collection,
            transformed_to_dl_compound,
            input_file,
            output_file
    ):

        root, files = sample_collection
        output_path, transform = transformed_to_dl_compound
        assert transform.called is True
        transform.assert_any_call(
            os.path.join(root, input_file),
            os.path.join(output_path, output_file),
            ANY
        )

    @pytest.fixture()
    def archival_transformed_to_ht_trust(
            self, sample_collection, monkeypatch):

        root, files = sample_collection
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        hathi_jp2_format = packager.PackageFactory(
            hathi_jp2_package.HathiJp2()
        )
        output_path = os.path.join('some', 'folder')
        transform = Mock()

        def mock_transform(_, source, destination):
            transform(source=source, destination=destination)

        with monkeypatch.context() as mp:
            mp.setattr(
                packager.transformations.Transformers,
                "transform", mock_transform
            )
            for package in factory.locate_packages(root):
                hathi_jp2_format.transform(package, output_path)

        return output_path, transform

    @pytest.mark.parametrize('input_file, output_file', [
        (
            os.path.join('access', '0001_002-004.tif'),
            os.path.join('0001_002', '00000004.jp2')
        ),
        (
            os.path.join('access', '0001_002-001.tif'),
            os.path.join('0001_002', '00000001.jp2'),
        ),
        (
            os.path.join('access', '0001_001-001.tif'),
            os.path.join('0001_001', '00000001.jp2'),
        ),
    ])
    def test_transform(
            self,
            sample_collection,
            archival_transformed_to_ht_trust,
            input_file, output_file):

        root, files = sample_collection
        output_path, transform = archival_transformed_to_ht_trust
        assert transform.called is True
        expected_destination = os.path.join(output_path, output_file)
        transform.assert_any_call(
            source=os.path.join(root, input_file),
            destination=expected_destination,
        )

    @pytest.fixture()
    def archival_full_name_transformed_to_ht_trust(
            self, sample_collection_longer, monkeypatch):

        root, files = sample_collection_longer
        factory = packager.PackageFactory(noneas.ArchivalNonEAS())
        hathi_jp2_format = packager.PackageFactory(
            hathi_jp2_package.HathiJp2()
        )
        output_path = os.path.join('some', 'folder')
        transform = Mock()

        def mock_transform(_, source, destination):
            transform(source=source, destination=destination)

        with monkeypatch.context() as mp:
            mp.setattr(
                packager.transformations.Transformers,
                "transform", mock_transform
            )
            for package in factory.locate_packages(root):
                hathi_jp2_format.transform(package, output_path)

        return output_path, transform

    @pytest.mark.parametrize('input_file, output_file', [
        (
            os.path.join('access', '0333_003_003_01-001.tif'),
            os.path.join('0333_003_003_01', '00000001.jp2')
        ),
        (
            os.path.join('access', '0333_003_003_01-002.tif'),
            os.path.join('0333_003_003_01', '00000002.jp2')
        ),
    ])
    def test_larger_transform(
            self,
            sample_collection_longer,
            archival_full_name_transformed_to_ht_trust,
            input_file, output_file):

        root, files = sample_collection_longer
        output_path, transform = archival_full_name_transformed_to_ht_trust
        assert transform.called is True
        expected_destination = os.path.join(output_path, output_file)
        transform.assert_any_call(
            source=os.path.join(root, input_file),
            destination=expected_destination,
        )


@pytest.mark.parametrize('file_name, group, part', [
    ('0001_001-002.tif', "0001_001", '002'),
    ('0001_001-001.tif', "0001_001", '001'),
    ('0001_002-001.tif', "0001_002", '001'),
    ('0001_002-002.tif', "0001_002", '002'),
    ('0333_003_003_01-001.tif', "0333_003_003_01", '001'),
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
def sample_cataloged_collection(
        monkeypatch
) -> typing.Tuple[str, typing.List[str]]:

    batch_root = os.path.join("dummy", "batch")
    number_of_sample_groups = 2
    number_of_parts_each = 4
    packages: typing.Set[str] = set()

    def scandir(_, path):

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

    monkeypatch.setattr(
        noneas.NonEASBuilder, 'locate_files_access',
        scandir
    )

    monkeypatch.setattr(
        noneas.NonEASBuilder, 'locate_files_preservation',
        scandir
    )

    for group_id in range(number_of_sample_groups):
        access_path = os.path.join(batch_root, "access")

        preservation_path = os.path.join(batch_root, "preservation")
        for part_id in range(number_of_parts_each):
            file_name = \
                f"991001{str(group_id + 1)}205899" \
                f"-" \
                f"{str(part_id + 1).zfill(3)}.tif"

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


class TestCatalogedTransformToHT:
    @pytest.fixture()
    def transformed_to_ht_trust(
            self, sample_cataloged_collection, monkeypatch, tmpdir
    ):
        transform = Mock()

        def mock_transform(_, source, destination):
            transform(source=source, destination=destination)

        root, files = sample_cataloged_collection
        factory = packager.PackageFactory(noneas.CatalogedNonEAS())
        digital_library_format = packager.PackageFactory(
            hathi_jp2_package.HathiJp2())
        output_path = os.path.join('some', 'folder')

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
            os.path.join('9910011205899', '00000002.jp2')
        ),
        (
            os.path.join('dummy', 'batch',
                         'access', '9910011205899-001.tif'),
            os.path.join('9910011205899', '00000001.jp2'),
        ),
        (
            os.path.join('dummy', 'batch',
                         'access', '9910012205899-001.tif'),
            os.path.join('9910012205899', '00000001.jp2'),
        ),
    ])
    def test_transform(
            self, transformed_to_ht_trust, input_file, output_file):
        output_path, transform = transformed_to_ht_trust
        assert transform.called is True
        expected_destination = os.path.join(output_path, output_file)
        transform.assert_any_call(
            source=input_file,
            destination=expected_destination,
        )


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
            monkeypatch.setattr(
                uiucprescon.packager.transformations.CopyFile,
                "transform",
                transform
            )
            monkeypatch.setattr(
                uiucprescon.packager.transformations.ConvertJp2Standard,
                "transform",
                transform
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
            self,
            transformed_to_dl_compound,
            input_file,
            output_file,
            monkeypatch
    ):

        output_path, transform = transformed_to_dl_compound
        assert transform.called is True
        expected_destination = os.path.join(output_path, output_file)
        assert \
            call(ANY, expected_destination, ANY) in \
            transform.call_args_list, \
            f"Expecting {expected_destination}. Found: {[x[0][1] for x in transform.call_args_list]}"

        assert \
            call(input_file, expected_destination, ANY) in \
            transform.call_args_list


class TestTransform:
    @pytest.fixture
    def cataloged_collection(self, monkeypatch):

        def factory(file_name):
            def locate_files_access(_, path):
                dir_entry = Mock()
                dir_entry.name = file_name
                dir_entry.path = os.path.join(path, "access")
                return [dir_entry]

            monkeypatch.setattr(
                uiucprescon.packager.packages.noneas.NonEASBuilder,
                "locate_files_access",
                locate_files_access
            )

            def locate_files_preservation(_, path):
                dir_entry = Mock()
                dir_entry.name = file_name
                dir_entry.path = os.path.join(path, "preservation")
                return [dir_entry]

            monkeypatch.setattr(
                uiucprescon.packager.packages.noneas.NonEASBuilder,
                "locate_files_preservation",
                locate_files_preservation
            )
            return "source"

        return factory

    @pytest.mark.parametrize(
        "source_file, package_type, expected_out",
        [
            (
                    '9910012205899-001.tif',
                    digital_library_compound.DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899', 'preservation',
                        '9910012205899-001.tif'
                    ),
            ),
            (
                    '9910012205899-001.tif',
                    digital_library_compound.DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899', 'access',
                        '9910012205899-001.jp2'
                    ),
            ),
            (
                    "9910012205899_1-001.tif",
                    digital_library_compound.DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899_1', 'preservation',
                        '9910012205899_1-001.tif'
                    ),
            ),
            (
                    "9910012205899_1-001.tif",
                    digital_library_compound.DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899_1', 'access',
                        '9910012205899_1-001.jp2'
                    ),
            ),
            (
                    '9910012205899-001.tif',
                    hathi_jp2_package.HathiJp2,
                    os.path.join('9910012205899', '00000001.jp2'),
            ),
            (
                    '9910012205899-001.tif',
                    hathi_jp2_package.HathiJp2,
                    os.path.join('9910012205899', '00000001.jp2'),
            ),
            (
                    "9910012205899_1-001.tif",
                    hathi_jp2_package.HathiJp2,
                    os.path.join('9910012205899_1', '00000001.jp2'),
            ),
            (
                    "9910012205899_1-001.tif",
                    hathi_jp2_package.HathiJp2,
                    os.path.join('9910012205899_1', '00000001.jp2'),
            )
        ]
    )
    def test_cataloged_collection_transform(
            self,
            cataloged_collection,
            source_file, package_type, expected_out,
            monkeypatch
    ):
        transform = Mock(spec=lambda source, destination: None)
        monkeypatch.setattr(
            uiucprescon.packager.transformations.Transformers,
            "transform",
            transform
        )

        transform2 = Mock(spec=lambda source, destination, logger: None)
        monkeypatch.setattr(
            uiucprescon.packager.transformations.CopyFile,
            "transform",
            transform2
        )
        monkeypatch.setattr(
            uiucprescon.packager.transformations.ConvertJp2Standard,
            "transform",
            transform2
        )

        output_dir = "output"
        factory = packager.PackageFactory(noneas.CatalogedNonEAS())
        for p in factory.locate_packages(cataloged_collection(source_file)):
            packager.PackageFactory(package_type()).transform(p, output_dir)

        if package_type == hathi_jp2_package.HathiJp2:
            transform.assert_any_call(
                ANY, os.path.join(output_dir, expected_out)
            )

        elif package_type == digital_library_compound.DigitalLibraryCompound:
            transform2.assert_any_call(
                ANY, os.path.join(output_dir, expected_out), ANY
            )
        else:
            assert False, f"testing '{package_type}' not supported"
