from setuptools import setup, find_packages
import io

setup(
    name="gitplm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=5.1",
    ],
    entry_points={
        'console_scripts': [
            'gitplm=gitplm.main:cli',
        ],
    },
    author="Python Version",
    description="A PLM (Product Lifecycle Management) tool based on Git",
    long_description=io.open("README.md", encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gitplm-python",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 