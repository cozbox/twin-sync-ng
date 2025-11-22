"""Setup file for TwinSync++ Python package."""
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install


class VerboseInstall(install):
    """Custom install command with verbose logging."""
    
    def run(self):
        """Run installation with verbose output."""
        print("=" * 60)
        print("Installing TwinSync++ - Device Configuration Manager")
        print("=" * 60)
        print("Finding packages...")
        
        # Run the actual installation
        install.run(self)
        
        print("\n" + "=" * 60)
        print("Installation Complete!")
        print("=" * 60)
        print("\nTwinSync++ has been installed successfully.")
        print("\nTo get started:")
        print("  1. Run 'twin' to launch the GUI")
        print("  2. Or use 'twin --help' for command-line options")
        print("  3. Run 'twin init' to initialize your first repository")
        print("\nFor more information, visit:")
        print("  https://github.com/cozbox/twin-sync-ng")
        print()


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
    cmdclass={
        'install': VerboseInstall,
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
