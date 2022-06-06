[![PyPI-Server](https://img.shields.io/pypi/v/munsellkit.svg)](https://pypi.python.org/pypi/munsellkit)
[![Build Status]](https://img.shields.io/travis/pzingg/munsellkit.svg)(https://travis-ci.com/pzingg/munsellkit)
[![Documentation Status](https://readthedocs.org/projects/munsellkit/badge/?version=latest)](https://munsellkit.readthedocs.io/en/latest/?version=latest)


# MunsellKit

Munsell color space tools

* Free software: MIT license
* Documentation: https://munsellkit.readthedocs.io.

## Requirements

To access features in the 'munsellkit.minterp' module, you must have
'Rscript' (part of the 'R' language) installed on your machine accessible
by a shell from Python ('Rscript' must be in your environment's `PATH`).

The R runtime must have the 'munsellinterpol' and 'jsonlite' packages
installed.

## Features

* TODO

## Installation and updates

For local install:

```
python3 setup.py install --user
```

When bumping version, change values in

* CHANGELOG.md,
* setup.cfg,
* setup.py and
* \_\_init\_\_.py.

## Credits

Colour Science for Python's **colour** Python package.
Available from https://www.colour-science.org

The R language **munsellinterpol** package.
Available from https://cran.r-project.org/web/packages/munsellinterpol/index.html

The **Pillow** Python imaging library, including the **ImageCms** color management module,
which is built on top of the **Little CMS** color engine.
Available from https://pillow.readthedocs.io/en/stable
And https://www.littlecms.com/color-engine

Paul Centore's **Colour Tools for Painters** website, and his **Munsell Resources** page.
Available from https://www.munsellcolourscienceforpainters.com

Bruce Lindbloom's **Uniform Perceptual LAB** color space and the ICC color management
profile file for converting to and from the UP LAB space.
Available from http://www.brucelindbloom.com/index.html?UPLab.html

This package was created with **Cookiecutter**<a href="#note1" id="note1ref"><sup>[1]</sup><a>
and the **audreyr/cookiecutter-pypackage**<a href="#note2" id="note2ref"><sup>[2]</sup><a>
project template.

<a id="note1" href="#note1ref"><sup>1</sup></a>Cookiecutter: https://github.com/audreyr/cookiecutter
<a id="note2" href="#note2ref"><sup>2</sup></a>audreyr/cookiecutter-pypackage: https://github.com/audreyr/cookiecutter-pypackage
