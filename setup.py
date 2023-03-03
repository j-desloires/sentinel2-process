import os
from setuptools import setup, find_packages


def parse_requirements(file):
    return sorted(
        (
            {
                line.partition("#")[0].strip()
                for line in open(os.path.join(os.path.dirname(__file__), file))
            }
            - set("")
        )
    )


setup(
    name="s2process",
    python_requires=">=3.7",
    version="1.0.0",
    description="Download Sentinel-2 data from Theia platform",
    author="Johann Desloires",
    author_email="johann.desloires@gmail.com",
    packages=find_packages(),
    package_data={"s2process": ["environment.yml"]},
)
