import os

from setuptools import find_packages, setup

from django_nextjs import __version__

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

dev_requirements = [
    "pre-commit",
    "pytest>=7",
    "pytest-cov",
    "pytest-django",
    "pytest-asyncio",
    "black",
    "isort",
]

LONG_DESCRIPTION = """
`django-nextjs` allows Django and Next.js pages to work together seamlessly.
It enables you to add Next.js pages to an existing Django project
or gradually migrate your frontend to Next.js.

**For full documentation, usage examples, and advanced configuration,
please visit the GitHub repository:**
[django-nextjs](https://github.com/QueraTeam/django-nextjs)
"""

setup(
    name="django-nextjs",
    version=__version__,
    description="Integrate Next.js into your Django project",
    long_description=LONG_DESCRIPTION.strip(),
    long_description_content_type="text/markdown",
    keywords=["django", "next", "nextjs", "django-nextjs"],
    author="Quera Team",
    url="https://github.com/QueraTeam/django-nextjs",
    download_url="https://github.com/QueraTeam/django-nextjs",
    packages=find_packages(".", include=("django_nextjs", "django_nextjs.*")),
    include_package_data=True,
    install_requires=["Django >= 4.2", "aiohttp", "websockets"],
    extras_require={"dev": dev_requirements},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
