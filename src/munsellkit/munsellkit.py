"""Convert between Munsell and RGB color spaces.

Various functions that convert from Munsell space to RGB space, using the 'colour'
package from Colour Science.
"""

import csv
import importlib.resources
import re
import numpy as np
import colour
from colour.notation import munsell as cnm

import munsellkit.minterpol as mint


# CIE 1931 2 Degree Standard Observers
# See https://patapom.com/blog/Colorimetry/Illuminants

# C is the standard illuminant for the original Munsell renotation
# ILLUMINANT_C = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['C']
ILLUMINANT_C = np.array([0.31006, 0.31616])

# D65 is the standard illuminant for the sRGB color space
# ILLUMINANT_D65 = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']
ILLUMINANT_D65 = np.array([0.31270, 0.32900])

# Letter codes corresponding to Colorlab's `hue_index`, a 1-based index.
COLORLAB_HUE_NAMES = [
    'B',  # hue_index  1, ASTM 60
    'BG', # hue_index  2, ASTM 50
    'G',  # hue_index  3, ASTM 40
    'GY', # hue_index  4, ASTM 30
    'Y',  # hue_index  5, ASTM 20
    'YR', # hue_index  6, ASTM 10
    'R',  # hue_index  7, ASTM  0
    'RP', # hue_index  8, ASTM 90
    'P',  # hue_index  9, ASTM 80
    'PB'  # hue_index 10, ASTM 70
]


def normalized_color(spec, rounding=1, truncate=True, out='all'): 
    """Normalize the color defined by a Colorlab specification.

    Parameters
    ----------
    spec : np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].
    rounding : int or 'renotation', default 1
      The number of decimal places to return in the 'total' item.
      If set to 'renotation' the hue_shade will be one of [0, 2.5, 5, 7.5].
      If omitted, no rounding will be done.
    truncate : boolean, default True
      If true, trailing '.0' are stripped from the hue and color strings 
      in the returned data.
    out : {'all','spec','color'}
      Determines the return value. If 'all', a three-tuple is returned.
      If 'spec' the normalized Colorlab specifcation is returned.
      If 'color' only the Munsell color notation is returned.

    Returns
    -------
    str
      The one- or two-letter code for the hue, like 'N' or 'PB'.
    
    Raises
    ------
    ValueError if the hue_index is not an integer in [0, 10].
    """
    hue_shade, value, chroma, hue_index = spec
    hue_index, hue_shade = normalized_hue(hue_index, hue_shade, rounding)
    if isinstance(rounding, str):
        if rounding != 'renotation':
            raise ValueError(f"Invalid rounding '{rounding}'")
        min_value = 1
        min_chroma = 2
        hue_decimals = 1
        value_decimals = 0
        chroma_decimals = 0
        value = round(value)
        chroma = round(chroma / 2) * 2
        if chroma < 2:
            # Coerce to neutral
            value = 0
    else:
        min_value = 0
        min_chroma = 0
        if rounding is not None:
            hue_decimals = rounding
            value_decimals = rounding
            chroma_decimals = rounding
            value = round(value, rounding)
            chroma = round(chroma, rounding)
        else:
            hue_decimals = 2
            value_decimals = 2
            chroma_decimals = 2

    value = max(min_value, min(value, 10))
    chroma = max(min_chroma, min(chroma, 50))
    if value == 0:
        # Rounded to neutral
        hue_index = np.nan
        hue_shade = np.nan
        chroma = np.nan

    norm_spec = np.array([hue_shade, value, chroma, hue_index])
    if out == 'spec':
        return norm_spec

    data = hue_data(hue_index, hue_shade, decimals=hue_decimals, truncate=truncate)
    if np.isnan(hue_index):
        cv = '{0:.{1}f}'.format(value, value_decimals)
    else:
        cv = '{0:.{1}f}/{2:.{3}f}'.format(value, value_decimals, chroma, chroma_decimals)
    if truncate:
        cv = re.sub(r'\.[0]+', '', cv)
    norm_color = ' '.join([data['total_hue'], cv])
    if out == 'color':
        return norm_color

    return (norm_color, norm_spec, data)


def normalized_hue(hue_index, hue_shade=None, rounding=1):
    """Round the hue to a specified precision.

    Parameters
    ----------
    hue_index : int
      The Colorlab Munsell specification `hue_index` in the domain [0, 10].
      Use `hue_index` 0 for neutral 'N'.
    hue_shade : float, required for non-neutrals
      The `hue_shade` in the domain [0, 10].
    rounding : int or 'renotation', default 1
      The number of decimal places to return in the 'total' item.
      If set to 'renotation' the hue_shade will be one of [0, 2.5, 5, 7.5].
      If omitted, no rounding will be done.

    Returns
    -------
    hue_index : float
      The `hue_index` possibly rounded.
    hue_shade : float
      The `hue_shade` possibly rounded.
    
    Raises
    ------
    ValueError if the hue_index is not an integer in [0, 10].
    """
    if np.isnan(hue_index):
        return (np.nan, np.nan)
    hue_index = int(hue_index)
    if hue_index == 0:
        return (np.nan, np.nan)
    if hue_index < 1 or hue_index > 10:
        raise ValueError(f'Invalid hue_index {hue_index}')
    if hue_shade is None:
        raise ValueError(f'hue_shade is required')
    if isinstance(rounding, str):
        if rounding != 'renotation':
            raise ValueError(f"Invalid rounding '{rounding}'")
        hue_shade = round(hue_shade / 2.5) * 2.5
    elif rounding is not None:
        hue_shade = round(hue_shade, rounding)
    hue_shade = max(0, min(hue_shade, 10))
    if hue_shade == 0:
        hue_shade = 10
        hue_index = (hue_index % 10) + 1
    return (float(hue_index), hue_shade)


def hue_name_from_hue_index(hue_index):
    """Get the hue name (letter code) corresponding to a Colorlab `hue_index`.

    Parameters
    ----------
    hue_index : int
      The Colorlab Munsell specification `hue_index` in the domain [0, 10].
      Use `hue_index` 0 for neutral 'N'.

    Returns
    -------
    str
      The one- or two-letter code for the hue, like 'N' or 'PB'.
    
    Raises
    ------
    ValueError if the hue_index is not an integer in [0, 10].
    """
    if np.isnan(hue_index):
        hue_index = 0
    h = int(hue_index)
    if h != hue_index or h < 0 or h > 10:
        raise ValueError(f'Invalid hue index {hue_index}')
    if h == 0:
        return 'N'
    return COLORLAB_HUE_NAMES[h-1]


def astm_hue(hue_index, hue_shade=None):
    """Get the ASTM hue value corresponding to a given Colorlab `hue_index`.

    Parameters
    ----------
    hue_index : int
      The Colorlab Munsell specification `hue_index` in the domain [0, 10].
      Use `hue_index` 0 for neutral.

    Returns
    -------
    int
      The ASTM hue value for the hue, in the domain [0, 90]. 
      'R' is 0, 'YR' is 10, etc. Returns 0 for 0 (neutral).

    Raises
    ------
    ValueError if the hue_index is not an integer in [0, 10].
    """
    if np.isnan(hue_index):
        hue_index = 0
    h = int(hue_index)
    if h != hue_index or h < 0 or h > 10:
        raise ValueError(f'Invalid hue index {hue_index}')      
    if h == 0:
        return 0
    if hue_shade is None:
        hue_shade = 0
    return 10 * ((17 - h) % 10) + hue_shade


def hue_data(hue_index, hue_shade=None, decimals=1, truncate=True):
    """Return various formats and parameters corresponding to a hue.

    Parameters
    ----------
    hue_index : int
      The Colorlab Munsell specification `hue_index` in the domain [0, 10].
      Use `hue_index` 0 for neutral 'N'.
    hue_shade : float, required for non-neutrals
      The `hue_shade` in the domain [0, 10].
    decimals : int, default 1
      The number of decimal places to return in the 'total_hue' item.

    Returns
    -------
    dict
      Information about the hue. Items in the dict:
    hue_name : str
      The one- or two-character code for the hue, like 'PB'
    total_hue : str
      The total code for the hue, like '2.5PB'.
    astm_hue : float
      The ASTM hue value in the domain [0, 100] 
    
    Raises
    ------
    ValueError if the hue_index is not an integer in [0, 10].
    """
    if np.isnan(hue_index) or hue_index == 0:
        return {'hue_name': 'N', 'total_hue': 'N', 'astm_hue': np.nan, }

    hue_name = hue_name_from_hue_index(hue_index)
    astm = astm_hue(hue_index, hue_shade)
    total = '{0:.{1}f}{2}'.format(hue_shade, decimals, hue_name)
    if truncate:
        total = re.sub(r'\.[0]+', '', total)
    return {'hue_name': hue_name, 'total_hue': total, 'astm_hue': astm}


def hue_index_from_hue_name(hue_name):
    """Get the Colorlab `hue_index` corresponding to a given hue name (letter code).

    Parameters
    ----------
    hue_name : str
      The one- or two-character name of the base hue, like 'N' or 'PB'.

    Returns
    -------
    int
      The Colorlab `hue_index` for the hue. 'B' is 1, 'BG' is 2, etc. 
      Returns 0 for 'N' (neutral).

    Raises
    ------
    ValueError if the name is not one of the 10 hues or 'N'.
    """
    name = name.strip().upper()
    if name == 'N':
        return 0.
    return COLORLAB_HUE_NAMES.index(name) + 1


def munsell_color_to_rgb(color):
    """Use the 'colour' package's xyY conversion, adjusting for Munsell illuminant C.
    
    Parameters
    ----------
    color : str
      A Munsell color name, like 'N5.5' or '5.8RP 7.3/4.5'.

    Returns
    -------
    np.ndarray of shape (3,) and dtype float
      (`r`, `g`, `b`) with `r`, `g`, and `b` in the domain [0, 1]
    """
    spec = cnm.munsell_colour_to_munsell_specification(color)
    return munsell_specification_to_rgb(spec)


def munsell_specification_to_rgb(spec):
    """Use the 'colour' package's xyY conversion, adjusting for Munsell illuminant C.
    
    Parameters
    ----------
    spec : np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].

    Returns
    -------
    np.ndarray of shape (3,) and dtype float
      (`r`, `g`, `b`) with `r`, `g`, and `b` in the domain [0, 1]

    Notes
    -----
    See https://www.munsellcolourscienceforpainters.com/MunsellResources/MunsellResources.html
    and https://stackoverflow.com/questions/3620663/color-theory-how-to-convert-munsell-hvc-to-rgb-hsb-hsl
    """
    # The first step is to convert the Munsell color to *CIE xyY* 
    # colorspace.
    xyY = cnm.munsell_specification_to_xyY(spec)

    # We then perform conversion to *CIE XYZ* tristimulus values.
    XYZ = colour.xyY_to_XYZ(xyY)

    # The last step will involve using the *Munsell Renotation System*
    # illuminant which is *CIE Illuminant C*:
    # http://nbviewer.ipython.org/github/colour-science/colour-ipython/blob/master/notebooks/colorimetry/illuminants.ipynb#CIE-Illuminant-C

    # It is necessary in order to ensure white stays white when
    # converting to *sRGB* colorspace and its different whitepoint 
    # (*CIE Standard Illuminant D65*) by performing chromatic 
    # adaptation between the two different illuminants.
    return colour.XYZ_to_sRGB(XYZ, ILLUMINANT_C)


def deprecated_rgb_to_munsell_specification(r, g, b):
    """Use the 'colour' package's xyY conversion, adjusting for Munsell illuminant C.
    
    Parameters
    ----------
    r, g, b : number in the domain [0, 255]

    Returns
    -------
    np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].

    Notes
    -----
    See https://www.munsellcolourscienceforpainters.com/MunsellResources/MunsellResources.html
    and https://stackoverflow.com/questions/3620663/color-theory-how-to-convert-munsell-hvc-to-rgb-hsb-hsl

    Use of this function is not recommended.

    The 'colour' package raises AssertionErrors for values outside the expected
    domains for value and chroma, and will also raise errors when no convergence 
    is found (usually for high-value, low-chroma colors).
    """
    rgb = np.array([r / 255, g / 255, b / 255])
    if rgb.max() == 0:
        return np.array([np.nan, 0, np.nan, np.nan])

    XYZ = colour.sRGB_to_XYZ(rgb, ILLUMINANT_C)
    xyY = colour.XYZ_to_xyY(XYZ)
    return xyY_to_munsell_specification(xyY)



def deprecated_xyY_to_munsell_specification(xyY):
    """Convert a color in xyY space to its Munsell equivalent.

    Parameters
    ----------
    xyY : np.ndarray of shape (3,) and dtype float
      The tristimulus values for the color, each in the domain [0, 1].

    Returns
    -------
    np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].

    Notes
    -----
    Use of this function is not recommended.

    The 'colour' package raises AssertionErrors for values outside the expected
    domains for value and chroma, and will also raise errors when no convergence 
    is found (usually for high-value, low-chroma colors).
    """
    v = Y_to_munsell_value(xyY[2])
    # if v < 1.0:
    #    return np.array([np.nan, v, np.nan, np.nan])

    # This can raise:
    # ColourUsageWarning: "<color>" is not within "MacAdam" limits for illuminant "C"
    return cnm.xyY_to_munsell_specification(xyY)


DATA_PACKAGE = 'munsellkit.data'

def neutrals():
    """Return a generator that reads the 'munsell_neutrals.csv' file.

    """
    with importlib.resources.open_text(DATA_PACKAGE, 'munsell_neutrals.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def Y_to_munsell_value(Y):
    """Get the Munsell `value` corresponding to an xyY `Y` luminosity.
    
    Use the 'colour' package's `munsell_value_ASTMD1535` function to 
    convert the `Y` luminosity value of the xyY color space in the domain [0, 1] 
    into the corresponding Munsell `value` in the domain [0, 10].
    """
    with colour.utilities.common.domain_range_scale('ignore'):
        return colour.notation.munsell_value_ASTMD1535(Y * 100)
