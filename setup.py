from setuptools import find_packages, setup

setup(
    name="pyblender",
    version="0.1.0",
    description="A small declarative layer over bpy to script Blender scenes",
    packages=find_packages(exclude=("examples",)),
    python_requires=">=3.9",
    install_requires=["numpy"],
    entry_points={"console_scripts": ["pyblender = pyblender.cmd:main"]},
)
