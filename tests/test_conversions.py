"""Tests for `munsellkit` module."""

import warnings
import pytest
import numpy as np
import colour
from colour.notation import munsell as cnm
import munsellkit as mkit
from munsellkit import minterpol as mint


HARD_COLORS = [
    ('Black Green', '020202'),
    ('Ivory Black', '090909'),
    ('Lamp Black', '0E0E0E'),
    ('Intense White', 'FEFBFB'),
    ('White', 'FEFCFC'),
    ('Burnt Sienna', '1E150F'),
    ('Bistre', '1B1714'),
    ('Naples Yellow', 'FEED40'),
    ('Nickel Yellow', 'FDF384'),
    ('Lemon Yellow', 'FBED28'),
    ('Bronze Green Deep', '161613'),
    ('Intense Blue', '0F1620')
]

REALPAINT_COLORS = [
    ('5YR 4.79/4.23', {
        'P3': (142.7, 110.7, 85.7),
        'sRGB': (148.7, 109.1, 81.6),
        'XYZ': (19.317, 17.911, 10.343),
        'xyY': (0.40607, 0.37651, 0.17911)}),
    ('9.7R 6.60/7.77', {
        'P3': (214.4, 148, 121.5),
        'sRGB': (226, 144.4, 116.2),
        'XYZ': (44.563, 37.496, 21.477),
        'xyY': (0.43041, 0.36216, 0.37496)})
]

def test_realpaint_to_munsell():
    for name, spaces in REALPAINT_COLORS:
        r, g, b = spaces['sRGB']
        spec = mint.rgb_to_munsell_specification(r, g, b)
        print(f'{name} {r:3.1f}, {g:3.1f}, {b:3.1f} -> interpol {spec}')
        color = cnm.munsell_specification_to_munsell_colour(spec)
        print(f'{name} {r:3.1f}, {g:3.1f}, {b:3.1f} -> interpol {color}')

def test_realpaint_from_munsell():
    for name, spaces in REALPAINT_COLORS:
        rgb_rp = np.array(spaces['sRGB'])
        rgb_csci = mkit.munsell_color_to_rgb(name)
        rgb_csci = rgb_csci * 255
        rgb_mint = mint.munsell_color_to_rgb(name)
        rgb_mint = rgb_mint * 255
        print(f'{name} -> rgb realpaint {rgb_rp}')
        print(f'{name} -> rgb colorsci {rgb_csci}')
        print(f'{name} -> rgb interpol {rgb_mint}')

