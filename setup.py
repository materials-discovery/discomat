from setuptools import setup, find_packages

setup(
    name="discomat",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyvis==0.3.2',
        'mnemonic',  # Add version if needed
        'rdflib==7.0.0',
        'setuptools~=65.5.0',
        'asttokens==2.4.1',
        'decorator==5.1.1',
        'executing==2.0.1',
    #    'ipython==8.26.0',
        'ipython==8.12.3', # Need this version for OMI
        'isodate==0.6.1',
        'jedi==0.19.1',
        'Jinja2==3.1.4',
        'jsonpickle==3.2.2',
        'MarkupSafe==2.1.5',
        'matplotlib-inline==0.1.7',
        #'networkx==3.3',
        'networkx==3.2.1', # Needed for OMI
        'parso==0.8.4',
        'pexpect==4.9.0',
        'prompt_toolkit==3.0.47',
        'ptyprocess==0.7.0',
        'pure_eval==0.2.3',
        'Pygments==2.18.0',
        'pyparsing==3.1.2',
        'six==1.16.0',
        'stack-data==0.6.3',
        'traitlets==5.14.3',
        'typing_extensions==4.12.2',
        'wcwidth==0.2.13'
    ],
)

