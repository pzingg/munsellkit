"""Tests for `munsellkit.lindbloom` module."""

import pytest
import numpy as np
import colour
from colour.notation import munsell as cnm
import munsellkit as mkit
from munsellkit import lindbloom


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

def print_spec(name, spec):
  hue_shade, value, chroma, hue_index = spec 
  color = cnm.munsell_specification_to_munsell_colour(spec)
  print(f'{name} -> hvc {hue_shade} {value} {chroma} {hue_index} -> {color}')

def test_inverse():
    for name in ['2.5G8/4', '5R6/6']:
      rgb = mkit.munsell_color_to_rgb(name)
      rgb = rgb * 255 
      lab1 = lindbloom.rgb_to_uplab(rgb[0], rgb[1], rgb[2])
      spec = lindbloom.uplab_to_munsell_specification(lab1)
      lab2 = lindbloom.munsell_specification_to_uplab(spec)
      print(f'{name} spec {spec}')
      print(f'{name} lab1 {lab1}')
      print(f'{name} lab2 {lab2}')
      np.testing.assert_array_almost_equal(lab1, lab2)

def test_color():
    for name in [
      'N6',
      '2.5R8/4',
      '2.5YR8/4',
      '2.5Y8/4',
      '2.5GY8/4',
      '2.5G8/4',
      '2.5BG8/4',
      '2.5B8/4',
      '2.5PB8/6',
      '2.5P8/4',
      '2.5RP8/4',
      '5RP8/4',  
      '7.5RP8/4',
      '10RP8/4', 
    ]:
        rgb = mkit.munsell_color_to_rgb(name) 
        if np.isnan(rgb[0]):
            print(f'{name} not available')
            continue
        rgb = rgb * 255
        spec1, spec2 = lindbloom.rgb_to_munsell_specification(rgb[0], rgb[1], rgb[2], with_renotation=True)
        print_spec(name, spec1)
        print_spec(f'{name} RENOTATION', spec2)
    for name, spaces in REALPAINT_COLORS:
        rgb = np.array(spaces['sRGB'])
        spec1, spec2 = lindbloom.rgb_to_munsell_specification(rgb[0], rgb[1], rgb[2], with_renotation=True)
        print_spec(name, spec1)
        print_spec(f'{name} RENOTATION', spec2)

def test_grays():
    for r, g, b in [(25*v, 25*v, 25*v) for v in range(0, 11)]:
        spec = lindbloom.rgb_to_munsell_specification(r, g, b)
        csci = cnm.munsell_specification_to_munsell_colour(spec)
        print(f'{r:3.1f}, {g:3.1f}, {b:3.1f} -> {csci}')
