from datetime import datetime
from os import getenv

from setuptools import find_packages, setup


def readme():
    with open("README.md") as f:
        content = f.read()
        return content


def requirements():
    with open("requirements.txt") as f:
        requirements_file = f.readlines()
    return [r.strip() for r in requirements_file]


setup(
    name="satisfactory-bot",
    version=getenv("BOT_VERSION", default=datetime.now().strftime("%Y.%m.%d.dev%H%M%S")),
    description="A Telegram bot to manage docker images for a satisfactory dedicated server ",
    long_description=readme(),
    url="https://github.com/ekeih/satisfactory-bot",
    author="Max Rosin",
    license="MIT",
    classifiers=["Programming Language :: Python :: 3"],
    python_requires=">=3",
    install_requires=requirements(),
    packages=find_packages(),
    entry_points={"console_scripts": ["satisfactory-bot=satisfactory.cli:cli"]},
)
