from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in property_manager/__init__.py
from property_manager import __version__ as version

setup(
    name="property_manager",
    version=version,
    description="Property management system for rental units with contracts and invoicing",
    author="Farah",
    author_email="farah@domain.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)

