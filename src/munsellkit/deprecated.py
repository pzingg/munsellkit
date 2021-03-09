"""Older work that is not useful, but might be in the future."""

import warnings
import numpy as np
import colour
from colour import notation, volume
import munsellkit as mkit


warnings.simplefilter('ignore', category=utilities.ColourUsageWarning)



def xyY_to_munsell_specification(xyY):
    """Use the 'colour' package to convert from xyY space to a Munsell color.

    Parameters
    ----------
    xyY : np.ndarray of shape (3,) and dtype float
        Its elements `x`, `y`, `Y` are numbers in the domain [0, 1].

    Returns
    -------
    np.ndarray of shape (4,) and dtype float
      A Colorlab-compatible Munsell specification (`hue_shade`, `value`, `chroma`, `hue_index`),
      with `hue_shade` in the domain [0, 10], `value` in the domain [0, 10], `chroma` in
      the domain [0, 50] and `hue_index` one of [1, 2, 3, ..., 10].
    """
    xyY_adjusted, value = _adjust_value_up(xyY)
    if value < 1:
        return np.array([np.nan, value, np.nan, np.nan])

    adjust_down = False
    try:
        munsell_spec = notation.munsell.xyY_to_munsell_specification(xyY_adjusted)
    except Exception as e:
        warnings.warn(str(e))
        adjust_down = True

    if adjust_down:
        xyY_adjusted, value, munsell_spec = _adjust_value_down(xyY_adjusted, value)
    return munsell_spec


def _adjust_to_macadam_limits(xyY):
    """Ensure that an xyY color is within the MacAdam limits.

    The `Y` value (luminosity) of the color is adjusted up towards 0.5 until the
    color is within the MacAdam limits.
    """
    if volume.is_within_macadam_limits(xyY, munsell.ILLUMINANT_NAME_MUNSELL):
        return xyY

    Y = xyY[2]
    xyY_temp = np.array(xyY)
    step = (0.5 - Y) / 100.
    for i in range(0, 100):
        xyY_temp[2] = Y + i * step
        if volume.is_within_macadam_limits(xyY_temp, munsell.ILLUMINANT_NAME_MUNSELL):
            warnings.warn(f'Y adjusted from {Y:.03f} to {xyY_temp[2]:.03f}')
            return xyY_temp

    raise RuntimeError(f'Could not adjust MacAdam for xyY {xyY}')


def _adjust_value_up(xyY):
    """Ensure that an xyY color will have a Munsell `value` within expected limits.

    The `Y` value (luminosity) is adjusted up towards 0.2 until the
    Munsell `value` for the color is in the domain [1, 10].
    """
    Y = xyY[2]

    # Already in domain '1'
    # Y = to_domain_1(Y)

    value = new_Y_to_munsell_value(Y)
    if value > 10:
        raise RuntimeError(f'Munsell value {value:.03f} exceeds 10 for xyY {xyY}')
    if Y == 0 or value >= 1:
        return (xyY, value)

    xyY_temp = np.array(xyY)
    step = (0.2 - Y) / 100.
    i = 1
    while i <= 100:
        Y_temp = Y + i * step
        new_value = new_Y_to_munsell_value(Y_temp)
        if new_value > 10:
            break
        if new_value >= 1:
            warnings.warn(f'Y adjusted up from {Y:.03f} to {Y_temp:.03f}: value from {value:.03f} to {new_value:.03f}')
            xyY_temp[2] = Y_temp
            return (xyY_temp, new_value)
        i += 1

    raise RuntimeError(f'Could not adjust Munsell value up for xyY {xyY}, last Y tested was {Y_temp:.03f}')


def _adjust_value_down(xyY, value):
    """Ensure that an xyY color will converge to a Munsell color during interpolation.

    The `Y` value (luminosity) is adjusted down towards 0.8 until the
    Munsell color is interpolated.
    """
    Y = xyY[2]

    # Already in domain '1'
    # Y = to_domain_1(Y)
    if Y < 0.8:
        raise RuntimeError(f'Xyy value {Y:.03f} is too low to adjust down')

    if value is None:
        value = new_Y_to_munsell_value(Y)
    if value > 10:
        raise RuntimeError(f'Munsell value {value:.03f} exceeds 10 for xyY {xyY}')

    xyY_temp = np.array(xyY)
    step = (0.8 - Y) / 100.
    i = 1
    while i <= 100:
        Y_temp = Y + i * step
        new_value = new_Y_to_munsell_value(Y_temp)
        if new_value > 10:
            break
        xyY_temp[2] = Y_temp
        try:
            munsell_spec = notation.munsell.xyY_to_munsell_specification(xyY_temp)
            warnings.warn(f'Y adjusted down from {Y:.03f} to {Y_temp:.03f}: value from {value:.03f} to {new_value:.03f}')
            return (xyY_temp, new_value, munsell_spec)
        except Exception as e:
            pass
        i = i + 1

    raise RuntimeError(f'Could not adjust Munsell value down for xyY {xyY}, last Y tested was {Y_temp:.03f}')
