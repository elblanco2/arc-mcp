from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arc-mcp-server",
    version="0.1.0",
    description="MCP server for deploying frameworks to hosting environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Arc Team",
    author_email="arc@example.com",
    url="https://github.com/elblanco2/arc-mcp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "mcp-sdk>=0.1.0",
        "cryptography>=38.0.0",
        "paramiko>=2.7.2",
        "aiohttp>=3.8.1"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "flake8>=4.0.0",
            "black>=22.0.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "arc=arc_mcp.server:main",
        ],
    },
)
