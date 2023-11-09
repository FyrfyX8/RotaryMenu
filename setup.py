import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as fh:
    requirements = [line.strip() for line in fh]

setuptools.setup(
    name="RPi.rotary-menu",
    version="1.0.0",
    author="Fynn Norbisrath",
    author_email="f.norbisrath@web-n-office.de",
    description="A Python library for Raspberry Pi to display and control a rotary menu on a LCD Char display.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    install_requires=requirements,
)