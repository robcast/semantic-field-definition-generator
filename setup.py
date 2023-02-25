import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="semantic-field-definition-generator", # Replace with your own username
    version="1.0.1rc1",
    author="Florian Kräutli, Robert Casties",
    author_email="florian.kraeutli@uzh.ch, casties@mpiwg-berlin.mpg.de",
    description="A generator for Field Definitions for ResearchSpace and Metaphacts",
    include_package=True,
    install_requires=['pybars3','PyYAML', 'rdflib'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robcast/semantic-field-definition-generator.git",
    packages=setuptools.find_namespace_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    scripts=["bin/semantic-field-util"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)