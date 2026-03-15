from setuptools import setup, find_packages

setup(
    name="v3x-zulfiqar-gideon",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.5.0",
        "edge-tts>=6.1.0",
    ],
    author="V3X",
    author_email="v3x@v3x.com",  # Placeholder for required field
    description="V3X ZULFIQAR-GIDEON: A sovereign, high-octane game framework for forging legends.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/v3x/zulfiqar-gideon", # Placeholder
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
