import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="thonny-lahendus",
    version="2.0.6",
    author="Priit Paluoja",
    author_email="priit.paluoja@gmail.com",
    description="Thonny plugin for lahendus.ut.ee",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kspar/easy-thonny",
    packages=setuptools.find_namespace_packages(),
    install_requires=[
        'easy-py>=0.3.7',
        'thonny>=3.2.7',
        'pillow>=8.0',
        'chevron>=0.13.1',
        'requests~=2.24.0'
    ],
    package_data={
        "thonnycontrib.easy": ["res/*.*", "templates/*.*"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
