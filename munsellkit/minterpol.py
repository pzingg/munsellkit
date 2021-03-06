"""Functions that use Rscript shell processes to convert Munsell colors
using the R 'munsellinterpol' package.
"""

import importlib.resources
import json
import shutil
import subprocess
import numpy as np


RSCRIPTS_PACKAGE = 'munsellkit.rscripts'


# 0-based index. hue 0 == 'R', hue 1 = 'YR', etc.
MUNSELLINTERPOL_HUE_NAMES = [
    'R',
    'YR',
    'Y',
    'GY',
    'G',
    'BG',
    'B',
    'PB',
    'P',
    'RP'
]


def rgb_to_munsell_specification(r, g, b):
    """Uses R 'munsellinterpol' package to convert from RGB to Munsell color.

      Parameters
    ----------
    r, g, b : number in the domain [0, 255]

    Returns
    -------
    """

    with importlib.resources.path(RSCRIPTS_PACKAGE, 'to_munsell.R') as rscript_path:
        out = subprocess.check_output([_rscript_executable_path(), 
            str(rscript_path), 'sRGB', str(r), str(g), str(b)])
    try:
        res = json.loads(out)
    except:
        res = None
    if not isinstance(res, list) or len(res) == 0:
        raise Exception(f"to_munsell.R returned unexpected output '{out}'")
    data = res[0]
    return _to_colorlab_specification(data)


def xyY_to_munsell_specification(xyY):
    """x, y, Y in [0, 1]"""

    x, y, Y = xyY

    with importlib.resources.path(RSCRIPTS_PACKAGE, 'to_munsell.R') as rscript_path:
        out = subprocess.check_output([_rscript_executable_path(), 
            str(rscript_path), 'xyY', str(x), str(y), str(Y * 100)])
    try:
        res = json.loads(out)
    except:
        res = None
    if not isinstance(res, list) or len(res) == 0:
        raise Exception(f"to_munsell.R returned unexpected output '{out}'")
    data = res[0]
    return _to_colorlab_specification(data)


def munsell_color_to_xyY(color, xyC='NBS'):
    with importlib.resources.path(RSCRIPTS_PACKAGE, 'munsell_to_xyy.R') as rscript_path:
        out = subprocess.check_output([_rscript_executable_path(), 
            str(rscript_path), color, xyC])
    try:
        res = json.loads(out)
    except:
        res = None
    if not isinstance(res, list) or len(res) == 0:
        raise Exception(f"munsell_to_xyy.R returned unexpected output '{out}'")
    data = res[0]
    return np.array(data)


def munsell_color_to_rgb(color):
    with importlib.resources.path(RSCRIPTS_PACKAGE, 'munsell_to_rgb.R') as rscript_path:
        out = subprocess.check_output([_rscript_executable_path(), 
            str(rscript_path), color])
    try:
        res = json.loads(out)
    except:
        res = None
    if not isinstance(res, list) or len(res) == 0:
        raise Exception(f"munsell_to_rgb.R returned unexpected output '{out}'")
    data = res[0]
    if data[0] == 'NA':
        return np.array([np.nan, np.nan, np.nan])
    return np.array(data) / 255


def _rscript_executable_path():
    return shutil.which('Rscript')


def _to_colorlab_specification(hvc):
    """Converts a Munsell color specification from the 'munsellinterpol' package into
    the Colorlab-compatible format.

    Parameters
    ----------
    hvc : array-like of shape (3,) and dtype float
      `hue`, `value`, and `chroma` as defined by the 'munsellinterpol' package.
    
    Returns
    -------
    np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].
    """

    hue, value, chroma = hvc
    if value <= 0 or chroma <= 0:
        # Grays
        # If error (value == -1), or value or chroma are zero, return black
        if value < 0:
            value = 0
        return np.array([np.nan, value, np.nan, np.nan])

    # Colors
    hue_shade, hue_index = _to_colorlab_hue(hue)
    return np.array([hue_shade, value, chroma, hue_index])


def _to_colorlab_hue(hue):
    """Converts single hue value from 'munsellinterpol' package into
    `hue_shade` and `hue_index` Colorlab values.

    Parameters
    ----------
    hue : float in domain [0, 100]

    Returns
    -------
    hue_shade, hue_index : float
      With `hue_shade` in domain [0, 10] and `hue_index` in domain [1, 10].
    """

    if hue == 0:
        hue = 100

    hue_index, hue_shade = divmod(hue, 10)
    hue_index = int(hue_index)
    if hue_shade == 0:
        hue_shade = 10
        hue_index = hue_index - 1

    # | code | munsellinterpol | Colorlab |
    # |    R |               0 |        7 |
    # |   YR |               1 |        6 |
    # |    Y |               2 |        5 |
    # |   GY |               3 |        4 |
    # |    G |               4 |        3 |
    # |   BG |               5 |        2 |
    # |    B |               6 |        1 |
    # |   PB |               7 |       10 |
    # |    P |               8 |        9 |
    # |   RP |               9 |        8 |
    hue_index = ((16 - hue_index) % 10) + 1
    return (hue_shade, hue_index)
