from setuptools import setup
import os


setup(
    packages=[
        'packager',
        'packager.packages',
    ],
    test_suite="tests",
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    zip_safe=False,
)
