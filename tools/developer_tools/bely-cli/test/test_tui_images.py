import sys
import unittest
from unittest.mock import patch

from bely_cli.tui import images


class WidgetForTests(unittest.TestCase):
    def test_off_returns_none(self):
        self.assertIsNone(images.widget_for({"auto": object()}, "off"))

    def test_empty_widgets_returns_none(self):
        self.assertIsNone(images.widget_for({}, "auto"))

    def test_unknown_mode_falls_back_to_auto(self):
        auto = object()
        self.assertIs(images.widget_for({"auto": auto}, "bogus"), auto)

    def test_none_mode_falls_back_to_auto(self):
        auto = object()
        self.assertIs(images.widget_for({"auto": auto}, None), auto)

    def test_explicit_mode_returns_its_class(self):
        auto, sixel = object(), object()
        widgets = {"auto": auto, "sixel": sixel}
        self.assertIs(images.widget_for(widgets, "sixel"), sixel)


class LoadImageWidgetsTests(unittest.TestCase):
    def test_missing_module_returns_empty_dict(self):
        with patch.dict(sys.modules, {"textual_image": None, "textual_image.widget": None}):
            self.assertEqual(images.load_image_widgets(), {})

    def test_returns_all_modes_when_available(self):
        fake_widget_module = type("m", (), {
            "Image": object(), "TGPImage": object(), "SixelImage": object(),
            "HalfcellImage": object(), "UnicodeImage": object(),
        })
        with patch.dict(sys.modules, {
            "textual_image": type("m", (), {})(),
            "textual_image.widget": fake_widget_module,
        }):
            widgets = images.load_image_widgets()
        self.assertEqual(set(widgets), set(images.IMAGE_MODES) - {"off"})
        self.assertIs(widgets["auto"], fake_widget_module.Image)
        self.assertIs(widgets["sixel"], fake_widget_module.SixelImage)


if __name__ == "__main__":
    unittest.main()
