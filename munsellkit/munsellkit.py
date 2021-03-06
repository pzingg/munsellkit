"""Functions that convert from Munsell space to RGB space, using the 'colour'
package.
"""

import numpy as np
import colour
from colour.notation import munsell as cnm


# CIE 1931 2 Degree Standard Observers
# See https://patapom.com/blog/Colorimetry/Illuminants

# C is the standard illuminant for the original Munsell renotation
# ILLUMINANT_C = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['C']
ILLUMINANT_C = np.array([0.31006, 0.31616])

# D65 is the standard illuminant for the sRGB color space
# ILLUMINANT_D65 = colour.CCS_ILLUMINANTS['CIE 1931 2 Degree Standard Observer']['D65']
ILLUMINANT_D65 = np.array([0.31270, 0.32900])

# 1-based index. hue_index 1 == 'B', hue_index 2 = 'BG', ... hue_index 10 = 'PB'
COLORLAB_HUE_NAMES = [
    'B',
    'BG',
    'G',
    'GY',
    'Y',
    'YR',
    'R',
    'RP',
    'P',
    'PB'
]


def munsell_color_to_rgb(color):
    """Uses the 'colour' package's xyY conversion, adjusting for Munsell illuminant C.
    
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
    """Uses the 'colour' package's xyY conversion, adjusting for Munsell illuminant C.
    
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
    """Uses the 'colour' package's xyY conversion, adjusting for Munsell illuminant C.
    
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
    v = new_Y_to_munsell_value(xyY[2])
    if v < 1.0:
        return np.array([np.nan, v, np.nan, np.nan])

    return cnm.xyY_to_munsell_specification(xyY)


def Y_to_munsell_value(Y):
    """Uses the 'colour' package's `munsell_value_ASTMD1535` function to 
    convert the `Y` luminosity value of the xyY color space in the domain [0, 1] 
    into the corresponding Munsell `value` in the domain [0, 10].
    """

    with utilities.common.domain_range_scale('ignore'):
        return notation.munsell_value_ASTMD1535(Y * 100)
