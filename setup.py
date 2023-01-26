from setuptools import setup

setup(
    packages=[
        'uiucprescon.packager',
        'uiucprescon.packager.packages',
    ],
    test_suite="tests",
    setup_requires=['pytest-runner'],
    install_requires=['py3exiv2bind>=0.1.9b1'],
    package_data={"uiucprescon.packager": ["py.typed"]},
    extras_require={"kdu": ['pykdu-compress>=0.1.7b2']},
    tests_require=['pytest', 'pytest-bdd<4.0'],
    zip_safe=False,
    python_requires='>=3.5',
)
