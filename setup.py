from setuptools import setup, find_packages

setup(
    name="discomat",
    version="0.01",
    packages=find_packages(),
    install_requires=[
        'pyvis',
        'mnemonic',
        'rdflib',
        'uuid'
    ],
)
