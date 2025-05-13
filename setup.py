from setuptools import setup, find_packages

setup(
    name="military-patient-generator",
    version="0.1.0",
    description="Generator for realistic patient data in military medical exercises",
    author="Markus Sandelin",
    author_email="markus@kingmuffin.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.0.0",
        "cryptography>=41.0.1",
        "faker>=18.10.1",
        "dicttoxml>=1.7.16",
        "aiofiles>=23.1.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.8",
)