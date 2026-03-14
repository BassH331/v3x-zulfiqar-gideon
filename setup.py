from setuptools import setup, find_packages

setup(
    name="v3x-zulfiqar-gideon",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.5.0",
        "edge-tts>=6.1.0",
    ],
    author="V3X Development Core",
    description="V3X ZULFIQAR-GIDEON: A sovereign, high-octane game framework forged to empower developers to create legends.",
    long_description="A high-performance Python game engine that decouples infrastructure from content, allowing developers to build, iterate, and deploy legends.",
    python_requires=">=3.8",
)
