from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='idfm_api',
    packages=find_packages(include=['idfm_api']),
    package_data={
        'idfm_api': ['lines.json'],
    },
    version='0.2.4',
    author='drosocode',
    license='MIT',
    description='API for Ile de france mobilite',
    url="https://github.com/droso-hass/idfm-api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["aiohttp", "async_timeout"],
    python_requires=">=3.7",
    project_urls={
        'Documentation': 'https://idfm-api.readthedocs.io/en/latest/',
        'Source': 'https://github.com/droso-hass/idfm-api',
    },
)
