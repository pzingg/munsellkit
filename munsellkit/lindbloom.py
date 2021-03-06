"""Functions that use Bruce Lindbloom's Uniform Perceptual LAB color space 
and ICC profile. See http://www.brucelindbloom.com/index.html?UPLab.html.
"""

import importlib.resources
import math
import numpy as np
from PIL import Image, ImageCms


DATA_PACKAGE = 'munsellkit.data'


# Chromatic adaptive transforms
# See http://brucelindbloom.com/index.html?Eqn_ChromAdapt.html
CAT_BRADFORD_D65_TO_C = np.array([
    [ 0.9821687, -0.0067531,  0.0518013],
    [-0.0044921,  0.9893393,  0.0162333],
    [ 0.0114719, -0.0199953,  1.2928395]])
CAT_BRADFORD_C_TO_D65 = np.array([
    [ 0.9904476, -0.0071683, -0.0116156],
    [-0.0123712,  1.0155950, -0.0029282],
    [-0.0035635,  0.0067697,  0.9181569]])


def rgb_to_munsell_specification(r, g, b, with_renotation=False):
    """Transforms a color in the sRGB color space to a Munsell color
    by way of the UP LAB color space.

    Parameters
    ----------
    r, g, b : number in the domain [0, 255]

    Returns
    -------
    np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].
    """

    lab = rgb_to_uplab(r, g, b)
    raw_spec = uplab_to_munsell_specification(lab)
    if with_renotation:
        renotated_spec = uplab_to_renotation_specification(raw_spec, lab)
        return (raw_spec, renotated_spec)
    else:
        return raw_spec


def rgb_to_uplab(r, g, b):
    """Transforms a color from the sRGB color space to the UP LAB color space.

    Parameters
    ----------
    r, g, b : number in the domain [0, 255]

    Returns
    -------
    np.ndarray of shape (3,) and dtype float
      The `l', `a-star` and `b-star` values for the color, with `l` in the domain [0, 1],
      and `a-star` and `b-star` each in the domain [-0.5, 0.5].

    Notes
    -----
    Uses ImageCms (LittleCMS technology) and Lindbloom's Uniform Perceptual LAB
    ICC profile. This technique seems to work more reliably than the Colour Science 
    algorithms, which choke and/or assert quite frequently.  However the LAB space
    that is used is only 8 bits per channel.
    """

    # Load the profiles and build a transform
    srgb_to_uplab_transform = _build_transform()

    # Make a 1-pixel image to be transformed.
    r = _clamp_8(r)
    g = _clamp_8(g)
    b = _clamp_8(b)
    rgb_image = Image.new('RGB', (1, 1), color=(r, g, b))

    # Create a new image by applying the transform object to the source image.
    uplab_image = ImageCms.applyTransform(
        im=rgb_image,
        transform=srgb_to_uplab_transform
    )
    ml, ma, mb = list(uplab_image.getdata())[0]
    # print(f'RGB {r} {g} {b} -> UPLAB {ml}, {ma}, {mb}'

    # This is undocumented, but it works
    # Normalize a and b in [-128, 127]
    a_star = ma - 128
    b_star = mb - 128

    lab = np.array([ml, a_star, b_star], dtype=float)
    lab = lab / 255

    # Now l is in [0, 1], and a and b are in [-0.5, 0.5]
    return lab


# Heuristic factors converting from l a* b* to value and chroma
VALUE_FACTOR = 9.9167
CHROMA_FACTOR = 50


def uplab_to_munsell_specification(lab):
    """Converts a point in the normalized UP LAB space to its equivalent Munsell color.

    Parameters
    ----------
    lab : np.ndarray of shape (3,) and dtype float
      The `l', `a-star` and `b-star` values for the color, with `l` in the domain [0, 1],
      and `a-star` and `b-star` each in the domain [-0.5, 0.5].

    Returns
    -------
    np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].
    """

    l, a_star, b_star = lab

    # Apply heuristics
    value = VALUE_FACTOR * l
    chroma = CHROMA_FACTOR * math.sqrt(a_star * a_star + b_star * b_star)

    # Grays
    if chroma < 0.01:
        return np.array([np.nan, value, np.nan, np.nan])

    hue_angle = math.atan2(b_star, a_star) * 180 / math.pi
    if hue_angle < 0:
        hue_angle = hue_angle + 360

    # Convert angles to Colorlab hues and hue_indexes
    # | Expect  | angle |   hue | (idx, sh) | index |
    # |  2.5 RP |     0 |   2.5 | (0,  2.5) |     8 | 
    # |  5.0 RP |     9 |   5.0 | (0,  5.0) |     8 | 
    # |  7.5 RP |    18 |   7.5 | (0,  7.5) |     8 | 
    # | 10.0 RP |    24 |  10.0 | (0, 10.0) |     8 | 
    # |  2.5 R  |    36 |  12.5 | (1,  2.5) |     7 |
    # ... 
    # |  2.5 P  |   324 |  92.5 | (9,  2.5) |     9 | 
    # |  5.0 P  |   333 |  95.0 | (9,  5.0) |     9 | 
    # |  7.5 P  |   342 |  97.5 | (9,  7.5) |     9 | 
    # | 10.0 P  |   351 | 100.0 | (9, 10.0) |     9 | 

    hue_0 = hue_angle * 100 / 360
    hue = hue_0 + 2.5
    if hue > 100:
        hue = hue - 100

    idx, hue_shade = divmod(hue, 10)
    idx = int(idx)
    if hue_shade == 0:
        hue_shade = 10
        idx = idx - 1
    hue_index = float((17 - idx) % 10) + 1
    spec = np.array([hue_shade, value, chroma, hue_index])
    # print(f'SPEC {spec} <- a* {a_star} b* {b_star} hue_angle {hue_angle} hue {hue}')

    return spec


def uplab_to_renotation_specification(spec, lab):
    """Converts a point in the normalized UP LAB space to its equivalent Munsell color.

    Parameters
    ----------
    lab : np.ndarray of shape (3,) and dtype float
      The `l', `a-star` and `b-star` values for the color, with `l` in the domain [0, 1],
      and `a-star` and `b-star` each in the domain [-0.5, 0.5].

    Returns
    -------
    np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` one of [0, 2.5, 5, 7.5], `value` one of [0, 1, 2, ..., 10], 
      `chroma` one of [0, 2, 4, ..., 50] and `hue_index` one of [1, 2, 3, ..., 10].

    Notes
    -----
    Measures the distance in the UP LAB a-b color plane at the given `l` (luminosity) value
    between the given `a*` and `b*` values and those of 4 bracketing `a*` and `b*` value
    pairs from the Munsell renotation (`hue_shade` of 2.5, 5, 7.5 and 10, and `chroma` one
    of [0, 2, 4, ..., 50]). Selects the one with the closest cartesian distance to the 
    given target.
    """

    hue_shade, value, chroma, hue_index = spec

    v_ren = value
    if v_ren < 1:
        v_ren = 1
    elif v_ren > 9 and v_ren < 9.9:
        v_ren = 9
    v_ren = round(v_ren)

    if np.isnan(hue_shade):
        # Grays
        spec[1] = v_ren
        return spec

    # Colors
    c0, _ = divmod(chroma, 2)
    c0 = c0 * 2
    c1 = c0 + 2
    h0, _ = divmod(hue_shade, 2.5)
    h0 = h0 * 2.5
    h1 = h0 + 2.5

    l, a_star, b_star = lab
    closest_dist = None
    closest = None
    for ct in [c0, c1]:
        for ht in [h0, h1]:
            test_spec = _normalized_specification(ht, value, ct, hue_index)
            lt, at, bt = munsell_specification_to_uplab(test_spec)
            distance_sq = (at - a_star) * (at - a_star) + (bt - b_star) * (bt - b_star)
            # print(f'test {test_spec}: distance is {distance_sq}')
            
            if closest_dist is None or closest_dist > distance_sq:
                closest_dist = distance_sq
                closest = test_spec

    closest[1] = v_ren
    return closest


def munsell_specification_to_uplab(spec):
    """Converts a Munsell color to its equivalent in the normalized UP LAB space.
    This function is the inverse of `uplab_to_munsell_specification`.

    Parameters
    ----------
    spec : np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in 
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].

    Returns
    -------
    np.ndarray of shape (3,) and dtype float
      The `l', `a-star` and `b-star` values for the color, with `l` in the domain [0, 1],
      and `a-star` and `b-star` each in the domain [-0.5, 0.5].
    """
    
    hue_shade, value, chroma, hue_index = spec

    if np.isnan(hue_shade):
        # Grays
        # Apply heuristics
        l = value / VALUE_FACTOR
        return np.array([l, 0, 0])

    hue_base = (18 - int(hue_index)) % 10
    hue = hue_base * 10 + hue_shade
    hue_0 = hue - 2.5
    if hue_0 < 0:
        hue_0 = hue_0 + 100
    hue_angle = hue_0 * 360 / 100

    # Apply heuristics
    l = value / VALUE_FACTOR
    radius = chroma / CHROMA_FACTOR

    hue_angle = hue_angle * math.pi / 180
    a_star = math.cos(hue_angle) * radius
    b_star = math.sin(hue_angle) * radius
    # print(f'INV {spec} -> a* {a_star} b* {b_star} hue_angle {hue_angle} hue {hue}')

    return np.array([l, a_star, b_star])


def _clamp_8(v):
    return int(min(255, max(0, v)))


def _normalized_specification(hue_shade, value, chroma, hue_index):      
    if hue_shade == 0:
        hue_shade = 10
        if hue_index > 9.9:
            hue_index = 1
        else:
            hue_index = hue_index + 1
    return np.array([hue_shade, value, chroma, hue_index])


def _build_transform():
    # Load UP LAB ICC profile from disk
    with importlib.resources.open_binary(DATA_PACKAGE, 'CIELab_to_UPLab.icc') as f:
        uplab_profile = ImageCms.getOpenProfile(f)

    # Create sRGB ICC profile in ImageCms package
    srgb_profile = ImageCms.createProfile(colorSpace='sRGB')

    # Create a transform object from the input and output profiles
    return ImageCms.buildTransform(
        inputProfile=srgb_profile,
        outputProfile=uplab_profile,
        inMode='RGB',
        outMode='LAB')
