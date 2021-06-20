import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "README.md"), "r", encoding="UTF-8") as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-nextjs",
    version="1.3.2",
    description="Next.js + Django integration",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Mohammad Javad Naderi",
    packages=find_packages(".", include=("nextjs", "nextjs.*")),
    include_package_data=True,
    install_requires=["Django>=3.1", "requests", "aiohttp", "channels", "django_js_reverse"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.1",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
    ],
)
