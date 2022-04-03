import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kfpdist",
    version="0.1.1",
    author="typhoonzero",
    author_email="typhoonzero@gmail.com",
    description="Use Kubeflow Pipeline to run distributed training jobs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/typhoonzero/kfp-dist-train",
    project_urls={
        "Bug Tracker": "https://github.com/typhoonzero/kfp-dist-train/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.6",
    install_requires=[
        'kubernetes',
        'kfp==1.7.1'
    ]
)
