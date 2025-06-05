from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the contents of your requirements file
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="prismedrive-cli",
    version="0.1.0",
    author="Your Name / Buzma", # Replace with your name or username
    author_email="your_email@example.com", # Replace with your email
    description="A CLI tool for interacting with PrismDrive API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your_username/prismedrive-cli", # Replace with your project's URL if available
    packages=find_packages(exclude=["tests*"]), # Finds 'prismedrive_cli'
    install_requires=requirements,
    python_requires=">=3.7", # Specify your minimum Python version
    entry_points={
        "console_scripts": [
            "prismdrive=prismedrive_cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha", # Or "4 - Beta", "5 - Production/Stable"
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License", # Choose your license
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent", # Or specify Linux if it's Linux-only
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities",
    ],
    keywords="prismdrive api cli cloud storage",
    project_urls={ # Optional
        "Bug Reports": "https://github.com/your_username/prismedrive-cli/issues",
        "Source": "https://github.com/your_username/prismedrive-cli/",
    },
)