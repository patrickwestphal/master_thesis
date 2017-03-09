from distutils.core import setup

setup(
    name='idanivanov.graphshingling',
    version='0.0.1',
    packages=['ivanov.graph'],
    scripts=['bin/graphshingling'],
    url='https://github.com/idanivanov/master_thesis',
    license='',
    author='Ivan Ivanov',
    author_email='',
    description='',
    tests_require=[
    ],
    install_requires=[
        'numpy',
        'scipy',
        'sklearn',
        'networkx',
        'matplotlib',
        'rdflib',
        'SPARQLWrapper',
        'unidecode'
    ],
)
