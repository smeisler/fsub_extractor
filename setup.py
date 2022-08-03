from distutils.core import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "fsub-extractor",
    packages = ["fsub-extractor"],
    version = "0.0.1",
    description = "Software that functionally segments white matter connections to generate task-specific subcomponents of fiber bundles.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author = "Steven Meisler",
    author_email = "smeisler@g.harvard.edu",
    url = "https://github.com/smeisler/fsub-extractor",
    download_url = "download link you saved (ADD THIS LATER)",
    keywords = ["dwi", "fmri", "white-matter-segmentation"],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering"
    ]
    # python_requires='>=3.8',  # TODO: UPDATE HERE!
    # install_requires=["dipy"]   # TODO: UPDATE HERE!
)
