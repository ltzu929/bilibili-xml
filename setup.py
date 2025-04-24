from setuptools import setup, find_packages

setup(
    name="bilibili-danmaku-analyzer",
    version="1.0.0",
    description="B站弹幕分析工具",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask",
        "requests",
        "jieba",
        "numpy",
        "scipy",
        "matplotlib",
    ],
    python_requires=">=3.6",
) 