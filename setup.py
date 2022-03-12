from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="metabase-manager",
    use_scm_version={
        "local_scheme": "dirty-tag",
        "write_to": "src/metabase_manager/_version.py",
        "fallback_version": "0.0.0",
    },
    description="Manage your Metabase instance programmatically.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Charles Lariviere",
    author_email="charleslariviere1@gmail.com",
    url="https://github.com/chasleslr/metabase-manager",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "metabase-python"
    ],
    extras_require={},
    setup_requires=[
        "setuptools_scm>=3.3.1",
    ],
    entry_points={
        "console_scripts": [
            "metabase-manager = metabase_manager.cli.main:cli"
        ]
    }
)
