"""Setup configuration for BELY MQTT Framework."""

from setuptools import find_packages, setup

setup(
    name="bely-mqtt-framework",
    version="0.1.0",
    description="Pluggable Python framework for handling BELY MQTT events",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="BELY Team",
    author_email="team@bely.dev",
    url="https://github.com/bely/mqtt-framework",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "click>=8.1.0",
        "paho-mqtt>=1.6.1",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pluggy>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "types-paho-mqtt>=1.6.0",
        ],
        "apprise": [
            "apprise>=1.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bely-mqtt=bely_mqtt.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Email",
        "Topic :: System :: Monitoring",
    ],
    keywords="mqtt bely logbook plugins framework",
)
