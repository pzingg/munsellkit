"""UP LAB color space conversions.

Functions that use Bruce Lindbloom's Uniform Perceptual LAB color space
and ICC profile. See http://www.brucelindbloom.com/index.html?UPLab.html.
"""

import importlib.resources
import math
import numpy as np
import colorspacious
from PIL import Image, ImageCms

import munsellkit

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
    """Transform a color in the sRGB color space to a Munsell color.

    The transformation is performed using by first converting the RGB color
    into the UP LAB color space, and then extracting the Munsell values
    from the UP LAB coordinates.

    Parameters
    ----------
    r, g, b : number in the domain [0, 255]

    with_renotaion : bool
        If True, return a tuple of the interpolated Munsell specification and
        a Munsell specification that is in the original Renotation.
        If False, returns just the interpolated Munsell specification.

    Returns
    -------
    np.ndarray of shape (4,) and dtype float (or 2-tuple of np.ndarray)
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].
    """
    r = _clamp_uint8(r)
    g = _clamp_uint8(g)
    b = _clamp_uint8(b)

    return _to_munsell_specification('RGB', (r, g, b), with_renotation)


def jch_to_munsell_specification(jch, with_renotation=False):
    """Convert a color in the CIECAM02 Jch space to its Munsell equivalent.

    Parameters
    ----------
    jch : np.ndarray of shape (3,) and dtype float
      The `J`, `C` and `h` values for the color, with `J` and `C` in the domain
      [0, 100] and `h` in the domain [0, 360].

    with_renotaion : bool
        If True, return a tuple of the interpolated Munsell specification and
        a Munsell specification that is in the original Renotation.
        If False, returns just the interpolated Munsell specification.

    Returns
    -------
    np.ndarray of shape (4,) and dtype float (or 2-tuple of np.ndarray)
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].

    Notes
    -----
    Do not use this. The conversion from JCh to Lab seems incorrect.
    Uses the colorspacious package.
    """
    jch_space = {
      'name': 'CIECAM02-subset',
      'axes': 'JCh',
      'ciecam02_space': colorspacious.CIECAM02Space.sRGB
    }
    lab_space = {
      'name': 'CIELab',
      'XYZ100_w': 'D65' # 'C'?
    }

    lab = colorspacious.cspace_convert(jch, jch_space, lab_space)
    # print(f'JCh {jch} -> lab {lab}')

    # LAB image format: 24-bit color, luminance, + 2 color channels
    # L is uint8, a, b are int8
    L = _clamp_uint8(lab[0])
    a = _clamp_int8(lab[1])
    b = _clamp_int8(lab[2])
    return _to_munsell_specification('LAB', (L, a, b), with_renotation)


# Heuristic factors converting from l a* b* to value and chroma
VALUE_FACTOR = 9.9167
CHROMA_FACTOR = 50


def uplab_to_munsell_specification(lab):
    """Convert a color in the normalized UP LAB space to its equivalent Munsell color.

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
    hue_index = (17 - int(idx)) % 10 + 1
    hue_index, hue_shade = munsellkit.normalized_hue(hue_index, hue_shade, rounding=None)
    spec = np.array([hue_shade, value, chroma, hue_index])
    # print(f'SPEC {spec} <- a* {a_star} b* {b_star} hue_angle {hue_angle} hue {hue}')

    return spec


def uplab_to_renotation_specification(spec, lab):
    """Convert a color in the normalized UP LAB space to its equivalent Munsell color.

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
            test_spec = munsellkit.normalized_color(
                np.array([ht, value, ct, hue_index]),
                rounding='renotation', out='spec')
            lt, at, bt = munsell_specification_to_uplab(test_spec)
            distance_sq = (at - a_star) * (at - a_star) + (bt - b_star) * (bt - b_star)
            # print(f'test {test_spec}: distance is {distance_sq}')

            if closest_dist is None or closest_dist > distance_sq:
                closest_dist = distance_sq
                closest = test_spec

    closest[1] = v_ren
    return closest


def munsell_specification_to_uplab(spec):
    """Convert a Munsell color to its equivalent in the normalized UP LAB space.

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


def _clamp_uint8(v):
    return min(255, max(0, int(v)))


def _clamp_int8(v):
    return min(-128, max(127, int(v)))


def _to_munsell_specification(mode, color, with_renotation):
    uplab = _to_uplab(mode, color)
    raw_spec = uplab_to_munsell_specification(uplab)
    if with_renotation:
        renotated_spec = uplab_to_renotation_specification(raw_spec, uplab)
        return (raw_spec, renotated_spec)
    else:
        return raw_spec


def _to_uplab(mode, color):
    """Transform a color from the sRGB or LAB color space to the UP LAB color space.

    Parameters
    ----------
    mode : {RGB, LAB}
      The color space to be transformed.
    color : 3-tuple of ints
      For 'RGB' space, `r`, `g`, `b` in the domain [0, 255].
      For 'LAB' space, `L`, `a`, `b` in the domain [0, 255].

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
    transform = _build_transform(mode)
    source_image = Image.new(mode, (1, 1), color=color)

    # Create a new image by applying the transform object to the source image.
    uplab_image = ImageCms.applyTransform(
        im=source_image,
        transform=transform
    )
    ml, ma, mb = list(uplab_image.getdata())[0]

    # This is undocumented, but it works
    # Normalize a and b in [-128, 127]
    a_star = ma - 128
    b_star = mb - 128

    lab = np.array([ml, a_star, b_star], dtype=float)
    lab = lab / 255

    # Now l is in [0, 1], and a and b are in [-0.5, 0.5]
    return lab


def _build_transform(mode):
    if mode == 'RGB':
        input_space = 'sRGB'
    else:
        input_space = mode

    # Create sRGB ICC profile in ImageCms package
    input_profile = ImageCms.createProfile(colorSpace=input_space)

    # Load UP LAB ICC profile from disk
    with importlib.resources.open_binary(DATA_PACKAGE, 'CIELab_to_UPLab.icc') as f:
        output_profile = ImageCms.getOpenProfile(f)

    # Create a transform object from the input and output profiles
    return ImageCms.buildTransform(
        inputProfile=input_profile,
        outputProfile=output_profile,
        inMode=mode,
        outMode='LAB')
