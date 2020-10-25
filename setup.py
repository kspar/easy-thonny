import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="thonny-easy",
    version="0.2.1",
    author="Priit Paluoja",
    author_email="priit.paluoja@gmail.com",
    description="Thonny plugin for lahendus.ut.ee",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kspar/easy-thonny",
    packages=setuptools.find_packages(),
    install_requires=[
        'easy-py>=0.2.0',
        'thonny>=3.2.7'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
