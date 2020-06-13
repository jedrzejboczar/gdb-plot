import setuptools

setuptools.setup(
    name='gdb_plot',
    version='0.0.1',
    author='Jędrzej Boczar',
    author_email='jedrzej.boczar@gmail.com',
    description='GDB plugin for interractive plotting',
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'numpy',
        'matplotlib',
        'pyparsing',
    ],
)
