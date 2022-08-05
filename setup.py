#from distutils.core import setup
from setuptools import setup, find_packages

#with open("README.md", "r") as fh:
#    long_description = fh.read()

setup(
    name = "fsub_extractor",
    packages = find_packages(),
    #packages = ["fsub-extractor"],
    version = "0.0.1"
    # python_requires='>=3.8',  # TODO: UPDATE HERE!
    # install_requires=["dipy"]   # TODO: UPDATE HERE!
)
