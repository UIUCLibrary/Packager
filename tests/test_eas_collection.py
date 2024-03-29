import os.path
import pathlib
from unittest.mock import Mock, call, ANY

import pytest

from uiucprescon import packager
from uiucprescon.packager.packages import eas, DigitalLibraryCompound, HathiJp2
from uiucprescon.packager.packages.collection import Batch


class TestEASCollection:
    @pytest.fixture()
    def sample_access_files(self):
        access_files = [
            "99338384012205899-00000001.tif",
            "99338384012205899-00000002.tif",
            "99350592312205899-00000001.tif",
            "99350592312205899-00000002.tif",
        ]
        return access_files

    @pytest.fixture()
    def sample_collection_path(self, sample_access_files, monkeypatch):
        batch_dir = "batch1"

        valid_paths = [
            batch_dir,
            os.path.join(batch_dir, "access")
        ]

        monkeypatch.setattr(
            packager.packages.eas.os.path,
            "exists", lambda path: path in valid_paths
        )

        monkeypatch.setattr(os, "makedirs", Mock())

        for f in sample_access_files:
            valid_paths.append(os.path.join(batch_dir, "access", f))

        def locate_files_access(_, path):
            for f in sample_access_files:
                new_file = Mock(
                    path=os.path.join(path, f),
                )
                new_file.name = f
                yield new_file

        monkeypatch.setattr(eas.EASBuilder,
                            "locate_files_access",
                            locate_files_access)

        def locate_package_files(_, path: str):
            for f in sample_access_files:
                yield pathlib.Path(os.path.join(path, f))

        monkeypatch.setattr(
            eas.EASBuilder,
            "locate_package_files",
            locate_package_files
        )

        return batch_dir

    def test_locate(self, sample_collection_path):
        factory = packager.PackageFactory(eas.Eas())
        packages = list(factory.locate_packages(sample_collection_path))
        assert len(packages) == 2

    @pytest.mark.parametrize("expected_source, expected_destination", [
        (
            os.path.join("batch1", "access", "99338384012205899-00000001.tif"),
            os.path.join("out", "99338384012205899", "00000001.jp2")
        ),
        (
            os.path.join("batch1", "access", "99338384012205899-00000002.tif"),
            os.path.join("out", "99338384012205899", "00000002.jp2")
        ),
        (
            os.path.join("batch1", "access", "99350592312205899-00000001.tif"),
            os.path.join("out", "99350592312205899", "00000001.jp2")
        ),
        (
            os.path.join("batch1", "access", "99350592312205899-00000002.tif"),
            os.path.join("out", "99350592312205899", "00000002.jp2")
        )
    ])
    def test_transform_to_hathi(self,
                                sample_collection_path,
                                expected_source,
                                expected_destination,
                                monkeypatch):

        factory = packager.PackageFactory(eas.Eas())
        packages = factory.locate_packages(sample_collection_path)
        destination_type = packager.PackageFactory(HathiJp2())
        output = "out"

        def spec(source, destination): pass
        transform = Mock(spec=spec)

        monkeypatch.setattr(
            packager.transformations.Transformers,
            "transform",
            transform
        )
        monkeypatch.setattr(
            packager.packages.hathi_jp2_package.pathlib.Path,
            "mkdir",
            Mock()
        )
        for p in packages:

            destination_type.transform(p, output)
            assert transform.called is True
        transform.assert_has_calls(
            [
                call(source=expected_source, destination=expected_destination)
            ]
        )

    def test_transform_to_dl(self, sample_collection_path, monkeypatch):
        factory = packager.PackageFactory(eas.Eas())
        packages = factory.locate_packages(sample_collection_path)
        destination_type = packager.PackageFactory(DigitalLibraryCompound())
        output = "out"

        transform = Mock()
        process = Mock()
        with monkeypatch.context() as mp:

            mp.setattr(
                packager.packages.digital_library_compound.UseAccessJp2ForAll,
                "process",
                process
            )
            mp.setattr(
                packager.transformations.Transformers,
                "transform",
                transform
            )

            for p in packages:
                destination_type.transform(p, output)
        calls = [
            call(
                source=os.path.join(
                    sample_collection_path,
                    "access",
                    "99338384012205899-00000001.tif"
                ),
                dest=os.path.join(
                    output,
                    "99338384012205899",
                    "preservation",
                    "99338384012205899-00000001.tif"
                ),
                strategy=ANY,
                logger=ANY
            ),
            call(
                source=os.path.join(
                    sample_collection_path,
                    "access",
                    "99338384012205899-00000002.tif"
                ),
                dest=os.path.join(
                    output,
                    "99338384012205899",
                    "access",
                    "99338384012205899-00000002.jp2"
                ),
                strategy=ANY,
                logger=ANY
            ),
            call(
                source=os.path.join(sample_collection_path,
                                    "access",
                                    "99338384012205899-00000002.tif"),
                dest=os.path.join(
                    output,
                    "99338384012205899",
                    "preservation",
                    "99338384012205899-00000002.tif"
                ),
                strategy=ANY,
                logger=ANY
            ),
            call(
                source=os.path.join(
                    sample_collection_path,
                    "access",
                    "99350592312205899-00000001.tif"
                ),
                dest=os.path.join(
                    output,
                    "99350592312205899",
                    "access",
                    "99350592312205899-00000001.jp2"
                ),
                strategy=ANY,
                logger=ANY
            ),
            call(
                source=os.path.join(
                    sample_collection_path,
                    "access",
                    "99350592312205899-00000001.tif"
                ),
                dest=os.path.join(
                    output,
                    "99350592312205899",
                    "preservation",
                    "99350592312205899-00000001.tif"
                ),
                strategy=ANY,
                logger=ANY
            ),
            call(
                source=os.path.join(
                    sample_collection_path,
                    "access",
                    "99350592312205899-00000002.tif"
                ),
                dest=os.path.join(
                    output,
                    "99350592312205899",
                    "access",
                    "99350592312205899-00000002.jp2"
                ),
                strategy=ANY,
                logger=ANY
            ),
            call(
                source=os.path.join(
                    sample_collection_path,
                    "access",
                    "99350592312205899-00000002.tif"
                ),
                dest=os.path.join(
                    output,
                    "99350592312205899",
                    "preservation",
                    "99350592312205899-00000002.tif"
                ),
                strategy=ANY,
                logger=ANY
            )
        ]
        for c in calls:
            assert c in process.mock_calls, \
                f"Expected: {c} found: {process.mock_calls}"


class TestEASBuilder:
    @pytest.fixture()
    def batch_dir(self, monkeypatch):

        # access/
        #   99338384012205899-00000001.tif
        #   99338384012205899-00000002.tif
        #   99338384012205899-00000003.tif
        #   99350592312205899-00000001.tif
        #   99350592312205899-00000002.tif

        root = os.path.join("fake", "path")
        valid_paths = [
            root,
            os.path.join(root, "access")
        ]

        monkeypatch.setattr(
            eas.os.path,
            "exists",
            lambda path: path in valid_paths
        )

        access_files = [
            "99338384012205899-00000001.tif",
            "99338384012205899-00000002.tif",
            "99338384012205899-00000003.tif",
            "99350592312205899-00000001.tif",
            "99350592312205899-00000002.tif",
        ]

        def scandir(path):
            for f in access_files:
                new_file = Mock(
                    path=os.path.join(path, f),
                )
                new_file.name = f
                yield new_file

        monkeypatch.setattr(eas.os, "scandir", scandir)

        def locate_package_files(_, path: str):
            for f in access_files:
                yield pathlib.Path(os.path.join(path, f))

        monkeypatch.setattr(
            eas.EASBuilder,
            "locate_package_files",
            locate_package_files
        )

        return root

    @pytest.fixture()
    def batch(self, batch_dir):
        builder = eas.EASBuilder()
        new_batch = Batch(batch_dir)
        builder.build_package(parent=new_batch, path=batch_dir)
        return new_batch

    def test_package_built(self, batch):
        assert len(batch.children[0]) == 2

    def test_build_package_invalid_no_access_directory(self, monkeypatch):
        builder = eas.EASBuilder()
        path = "dummy"

        monkeypatch.setattr(eas.os.path, "exists", lambda path: False)
        with pytest.raises(FileNotFoundError) as e:
            builder.build_package(parent=Mock(), path=path)
        assert "No access directory locate" in str(e.value)

    def test_locate_package_files(self, monkeypatch):
        path = "dummy"
        builder = eas.EASBuilder()

        def search_strategy(path):
            return [
                Mock(path=os.path.join(path, "99338384012205899-00000001.tif"))
            ]
        p = next(
            builder.locate_package_files(path, search_strategy=search_strategy)
        )

        assert p == pathlib.Path(
            os.path.join("dummy", "99338384012205899-00000001.tif")
        )

    def test_object_has_items(self, batch):
        package_object = batch.children[0].children[0]
        assert len(package_object) == 3

    def test_item_instances(self, batch):
        package_item = batch.children[0].children[0].children[0]
        assert len(package_item) == 1

    @pytest.mark.parametrize("file_name, is_eas", [
        ("99338384012205899-00000001.tif", True),
        ("99338384012205899-00000002.tif", True),
        ("99350592312205899-00000001.tif", True),
        ("99350592312205899-00000002.tif", True),
        ("99350592312205899_00000002.tif", False),
        ("abc50592312205899-00000002.tif", False),
        (os.path.join("batch1", "access"), False),
    ])
    def test_is_eas_file(self, file_name, is_eas):
        builder = eas.EASBuilder()
        assert builder.is_eas_file(pathlib.Path(file_name)) is is_eas

    def test_is_eas_file_invalid_dir(self, monkeypatch):
        builder = eas.EASBuilder()
        path = os.path.join("batch1", "access", "99350592312205899-00000002")
        monkeypatch.setattr(eas.pathlib.Path, "is_dir", lambda _: True)
        assert builder.is_eas_file(pathlib.Path(path)) is False


class TestTransform:
    @pytest.fixture
    def eas_collection(self, monkeypatch):

        def factory(file_name):
            def locate_files_access(_, path):
                dir_entry = Mock()
                dir_entry.name = file_name
                dir_entry.path = os.path.join(path, "access")
                return [dir_entry]

            monkeypatch.setattr(
                eas.EASBuilder,
                "locate_files_access",
                locate_files_access
            )

            def locate_package_files(_, path):
                pres_entry = Mock()
                pres_entry.name = file_name
                pres_entry.path = os.path.join(path, "preservation")
                access_entry = Mock()
                access_entry.name = file_name
                access_entry.path = os.path.join(path, "access")
                return [pres_entry, access_entry]

            monkeypatch.setattr(
                eas.EASBuilder,
                "locate_package_files",
                locate_package_files
            )
            monkeypatch.setattr(eas.os.path, "exists", lambda x: True)
            return "source"

        return factory

    @pytest.mark.parametrize(
        "source_file, package_type, expected_out",
        [
            (
                    '9910012205899-000002.tif',
                    DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899', 'preservation',
                        '9910012205899-000002.tif'
                    ),
            ),
            (
                    '9910012205899-001.tif',
                    DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899', 'access',
                        '9910012205899-001.jp2'
                    ),
            ),
            (
                    "9910012205899_1-001.tif",
                    DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899_1', 'preservation',
                        '9910012205899_1-001.tif'
                    ),
            ),
            (
                    "9910012205899_1-001.tif",
                    DigitalLibraryCompound,
                    os.path.join(
                        '9910012205899_1', 'access',
                        '9910012205899_1-001.jp2'
                    ),
            ),
            (
                    '9910012205899-001.tif',
                    HathiJp2,
                    os.path.join('9910012205899', '00000001.jp2'),
            ),
            (
                    '9910012205899-001.tif',
                    HathiJp2,
                    os.path.join('9910012205899', '00000001.jp2'),
            ),
            (
                    "9910012205899_1-001.tif",
                    HathiJp2,
                    os.path.join('9910012205899_1', '00000001.jp2'),
            ),
            (
                    "9910012205899_1-001.tif",
                    HathiJp2,
                    os.path.join('9910012205899_1', '00000001.jp2'),
            )
        ]
    )
    def test_cataloged_collection_transform(
            self,
            eas_collection,
            source_file, package_type, expected_out,
            monkeypatch
    ):
        transform = Mock(spec=lambda source, destination: None)
        monkeypatch.setattr(
            packager.transformations.Transformers,
            "transform",
            transform
        )
        output_dir = "output"
        factory = packager.PackageFactory(eas.Eas())
        for p in factory.locate_packages(eas_collection(source_file)):
            packager.PackageFactory(package_type()).transform(p, output_dir)
