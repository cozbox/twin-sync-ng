"""Setup file for TwinSync++ Python package."""
from setuptools import setup, find_packages

setup(
    name="twin-sync",
    version="0.0.0",
    description="TwinSync++ - Git-backed device configuration management",
    author="TwinSync Contributors",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "PyYAML",
        "jsonschema",
    ],
    entry_points={
        "console_scripts": [
            "twin=twin_core.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
