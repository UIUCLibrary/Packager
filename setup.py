from setuptools import setup
import os


setup(
    packages=['packager'],
    test_suite="tests",
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    entry_points={
         "console_scripts": [
             'packager = packager.__main__:main'
         ]
     },
    zip_safe=False,
)
