"""
Setup script for Arc MCP Server.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arc-mcp",
    version="0.1.0",
    author="elblanco2",
    author_email="122809544+elblanco2@users.noreply.github.com",
    description="Arc MCP Server - Simplified web application deployment through conversational interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elblanco2/arc-mcp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=0.1.0",
        "paramiko>=2.7.0",
        "cryptography>=3.4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=20.8b1",
            "isort>=5.7.0",
            "flake8>=3.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "arc=arc.__main__:main",
        ],
    },
)
