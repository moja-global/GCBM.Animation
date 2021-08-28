# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
    name="gcbmanimation",
    version="1.0",
    description="GCBM Animator",
    long_description="GCBM Animator",
    url="",
    author="Moja.global",
    author_email="",
    license="MPL2",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: Mozilla Public License 2.0",
        "Programming Language :: Python :: 3",
    ],
    keywords="moja.global",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=["numpy", "matplotlib", "seaborn", "imageio", "imageio-ffmpeg", "pillow", "geopy", "pysal<=1.15.0", "utm"],
    extras_require={},
    package_data={},
    data_files=[],
    entry_points={
        "console_scripts": [
            "gcbmanimation = gcbmanimation.scripts.animate:cli"
        ]
    },
    python_requires=">=3.7"
)
