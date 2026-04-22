import tempfile
import unittest
from pathlib import Path

from PIL import Image

from sb3topy.unpacker.convert_svg import normalize_png_alpha


class SvgConversionTests(unittest.TestCase):
    def test_normalize_png_alpha_bleeds_only_transparent_edge_pixels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "asset.png"
            image = Image.new("RGBA", (3, 1))
            image.putpixel((0, 0), (0, 0, 0, 0))
            image.putpixel((1, 0), (0, 0, 0, 0))
            image.putpixel((2, 0), (200, 100, 50, 255))
            image.save(image_path)

            normalize_png_alpha(image_path)

            normalized = Image.open(image_path).convert("RGBA")
            self.assertEqual(normalized.getpixel((0, 0)), (0, 0, 0, 0))
            self.assertEqual(normalized.getpixel((1, 0)), (200, 100, 50, 0))
            self.assertEqual(normalized.getpixel((2, 0)), (200, 100, 50, 255))

    def test_normalize_png_alpha_converts_rgb_png_to_rgba(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "asset.png"
            Image.new("RGB", (1, 1), (10, 20, 30)).save(image_path)

            normalize_png_alpha(image_path)

            normalized = Image.open(image_path)
            self.assertEqual(normalized.mode, "RGBA")
            self.assertEqual(normalized.getpixel((0, 0)), (10, 20, 30, 255))

    def test_normalize_png_alpha_clears_uniform_opaque_edge_background(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "asset.png"
            image = Image.new("RGB", (5, 5), (12, 34, 56))
            image.putpixel((2, 2), (200, 100, 50))
            image.save(image_path)

            normalize_png_alpha(image_path)

            normalized = Image.open(image_path).convert("RGBA")
            self.assertEqual(normalized.getpixel((0, 0)), (12, 34, 56, 0))
            self.assertEqual(normalized.getpixel((1, 1)), (200, 100, 50, 0))
            self.assertEqual(normalized.getpixel((2, 2)), (200, 100, 50, 255))

    def test_normalize_png_alpha_clears_uniform_rgba_edge_background(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "asset.png"
            image = Image.new("RGBA", (5, 5), (12, 34, 56, 255))
            image.putpixel((2, 2), (200, 100, 50, 255))
            image.save(image_path)

            normalize_png_alpha(image_path)

            normalized = Image.open(image_path).convert("RGBA")
            self.assertEqual(normalized.getpixel((0, 0)), (12, 34, 56, 0))
            self.assertEqual(normalized.getpixel((1, 1)), (200, 100, 50, 0))
            self.assertEqual(normalized.getpixel((2, 2)), (200, 100, 50, 255))


if __name__ == "__main__":
    unittest.main()
