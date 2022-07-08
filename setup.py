from setuptools import find_packages, setup

setup(
    name="pyblender",
    version="0.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pyblender = pyblender.cmd:main"
        ]
    }
)
