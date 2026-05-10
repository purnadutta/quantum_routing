from setuptools import setup, find_packages

setup(
    name="quantum_routing",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy",
        "networkx",
        "pyyaml",
        "matplotlib",
    ],
    python_requires=">=3.8",
)
