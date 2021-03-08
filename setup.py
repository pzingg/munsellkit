#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.md') as changelog_file:
    changelog = changelog_file.read()

requirements = [ ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Peter Zingg",
    author_email='peter.zingg@gmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Munsell color space tools",
    entry_points={
        'console_scripts': [
            'munsellkit=munsellkit.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + changelog,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords='munsellkit',
    name='munsellkit',
    packages=find_packages(where='src', include=['munsellkit', 'munsellkit.*']),
    package_dir={'': 'src'},
    # project_urls={'Bug Tracker': https://github.com/pypa/sampleproject/issues},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/pzingg/munsellkit',
    version='0.1.0',
    zip_safe=False,
)
