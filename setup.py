from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="qpds",
    version="1.0.0",
    author="QPDS Team",
    description="Quantitative Poker Decision System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/QPDS",
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "Flask>=2.3.0",
        "redis>=4.6.0",
        "psycopg2-binary>=2.9.0",
        "treys>=0.1.8",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "lightgbm>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "qpds=api.app:main",
        ],
    },
)