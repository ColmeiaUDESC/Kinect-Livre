import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import projecao_visual as visual

LAYOUT = '(0, 0, 1), -100\n(-40, -30, -100)\n(40, -30, -100)\n(-40, 30, -100)\n(40, 30, -100)\n'
IDENTITY = struct.pack('<16d', 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


class VisualTests(unittest.TestCase):
    def test_full_turn_is_unchanged(self):
        self.assertEqual(visual.rotated_projection(IDENTITY, 360, 16 / 9), IDENTITY)
        self.assertEqual(visual.preview_view(LAYOUT, 360), visual.preview_view(LAYOUT, 0))

    def test_clockwise_quarter_turn_preserves_pixel_distances(self):
        matrix = struct.unpack('<16d', visual.rotated_projection(IDENTITY, 90, 16 / 9))
        x, y = 0.1, 0.2
        xp = matrix[0] * x + matrix[1] * y
        yp = matrix[4] * x + matrix[5] * y
        self.assertAlmostEqual(xp * 1920 / 2, y * 1080 / 2)
        self.assertAlmostEqual(yp * 1080 / 2, -x * 1920 / 2)
        self.assertEqual(matrix[8:], struct.unpack('<16d', IDENTITY)[8:])

    def test_four_quarter_turns_restore_projection(self):
        data = IDENTITY
        for _ in range(4):
            data = visual.rotated_projection(data, 90, 16 / 9)
        for a, b in zip(struct.unpack('<16d', data), struct.unpack('<16d', IDENTITY)):
            self.assertAlmostEqual(a, b)

    def test_preview_center_size_and_orientation(self):
        header = b'Vrui viewpoint file v1.0\n'
        for angle in (0, 90, 180, 270, 360, 37):
            data = visual.preview_view(LAYOUT, angle)
            self.assertTrue(data.startswith(header))
            values = struct.unpack('<10d', data[len(header):])
            self.assertEqual(values[:4], (0, 0, -100, 50))
            forward, up = values[4:7], values[7:]
            self.assertAlmostEqual(sum(a * b for a, b in zip(forward, up)), 0)
            self.assertAlmostEqual(sum(a * a for a in up), 1)
        up = struct.unpack('<10d', visual.preview_view(LAYOUT, 90)[len(header):])[7:]
        self.assertEqual(up, (-1, 0, 0))

    def test_smaller_view_keeps_center_and_orientation(self):
        header = b'Vrui viewpoint file v1.0\n'
        original = struct.unpack('<10d', visual.preview_view(LAYOUT, 90)[len(header):])
        reduced = struct.unpack('<10d', visual.preview_view(LAYOUT, 90, 75)[len(header):])
        self.assertEqual(original[:3], reduced[:3])
        self.assertEqual(original[4:], reduced[4:])
        self.assertAlmostEqual(reduced[3], original[3] / 0.75)
        for size in (0, -1, 151, math.nan):
            with self.assertRaises(ValueError): visual.preview_view(LAYOUT, 0, size)

    def test_bad_input_rejected(self):
        for angle in (math.nan, math.inf):
            with self.assertRaises(ValueError):
                visual.rotation_terms(angle)
        with self.assertRaises(ValueError):
            visual.rotated_projection(b'bad', 90, 1)
        with self.assertRaises(ValueError):
            visual.preview_view(LAYOUT.replace('(0, 0, 1)', '(0, 0, 0)'), 90)

    def test_modes_preserve_original_calibration(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            config, state = base / 'config', base / 'state'
            config.mkdir()
            state.mkdir()
            (config / 'BoxLayout.txt').write_text(LAYOUT)
            settings = {**visual.DEFAULTS, 'rotacao': 90}
            options, _ = visual.orientation_options(config, state, settings, None)
            self.assertEqual(options[0], '-loadView')
            original = config / 'ProjectorMatrix.dat'
            original.write_bytes(IDENTITY)
            with patch.object(visual, 'screen_aspect', return_value=16 / 9):
                options, _ = visual.orientation_options(config, state, settings, 'screen')
            self.assertEqual(options[0], '-fpv')
            self.assertEqual(original.read_bytes(), IDENTITY)
            self.assertNotEqual(Path(options[1]).read_bytes(), IDENTITY)

    def test_normal_appearance(self):
        self.assertEqual(visual.appearance_options(visual.DEFAULTS), ['-uhs', '-ucl'])
        self.assertEqual(visual.appearance_options({'relevo': False, 'curvas': False}), ['-nhs', '-ncl'])


if __name__ == '__main__':
    unittest.main()
