from setuptools import setup
import os


setup(
    packages=[
        'uiucprescon.packager',
        'uiucprescon.packager.packages',
    ],
    namespace_packages=["uiucprescon"],
    test_suite="tests",
    setup_requires=['pytest-runner'],
    install_requires=["py3exiv2bind>=0.1.2"],
    extras_require={"kdu": ['pykdu-compress>=0.1.0']},
    tests_require=['pytest'],
    zip_safe=False,
    python_requires='>=3.5',
)
