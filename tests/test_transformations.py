import os.path
from unittest.mock import Mock, ANY

from uiucprescon import packager


def test_convert_jp2_hathi_source(monkeypatch):

    import pykdu_compress
    kdu_compress_cli2 = Mock()
    monkeypatch.setattr(pykdu_compress, "kdu_compress_cli2", kdu_compress_cli2)
    monkeypatch.setattr(packager.transformations, "set_dpi", Mock())
    logger = Mock()
    transformer = packager.transformations.ConvertJp2Hathi()
    transformer.transform(
        "somefile.tif",
        destination="someoutput.jp2",
        logger=logger)
    assert kdu_compress_cli2.called is True
    kdu_compress_cli2.assert_called_with(
        infile="somefile.tif",
        outfile="someoutput.jp2",
        in_args=ANY
    )


def test_convert_jp2_hathi_user_dir_for_output(monkeypatch):

    import pykdu_compress
    kdu_compress_cli2 = Mock()
    monkeypatch.setattr(pykdu_compress, "kdu_compress_cli2", kdu_compress_cli2)
    monkeypatch.setattr(packager.transformations, "set_dpi", Mock())
    logger = Mock()
    transformer = packager.transformations.ConvertJp2Hathi()

    destination = os.path.join(os.getcwd(), "out", os.path.sep)
    transformer.transform(
        "somefile.tif",
        destination=destination,
        logger=logger)
    assert kdu_compress_cli2.called is True
    kdu_compress_cli2.assert_called_with(
        infile="somefile.tif",
        outfile=os.path.join(destination, "somefile.jp2"),
        in_args=ANY
    )
