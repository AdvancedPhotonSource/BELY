import unittest

from bely_cli.tui.mdimages import attachment_name, split_entry_markdown


class AttachmentNameTests(unittest.TestCase):
    def test_log_attachments_prefix(self):
        self.assertEqual(
            attachment_name("/log/attachments/attachment.1.png"), "attachment.1.png")

    def test_api_downloads_prefix(self):
        self.assertEqual(
            attachment_name("/api/Downloads/Attachments/attachment.1.jpg"),
            "attachment.1.jpg")

    def test_case_insensitive_extension_but_preserves_name_case(self):
        self.assertEqual(
            attachment_name("/log/attachments/Attachment.1.PNG"), "Attachment.1.PNG")

    def test_non_image_attachment_rejected(self):
        self.assertIsNone(attachment_name("/log/attachments/report.pdf"))

    def test_external_url_rejected(self):
        self.assertIsNone(attachment_name("https://example.com/x.png"))

    def test_unrelated_path_rejected(self):
        self.assertIsNone(attachment_name("/some/other/path.png"))

    def test_empty_or_none(self):
        self.assertIsNone(attachment_name(""))
        self.assertIsNone(attachment_name(None))


class SplitEntryMarkdownTests(unittest.TestCase):
    def test_plain_text_returns_single_markdown_segment(self):
        text = "Just some text with no images."
        self.assertEqual(split_entry_markdown(text), [("markdown", text)])

    def test_empty_and_none(self):
        self.assertEqual(split_entry_markdown(""), [("markdown", "")])
        self.assertEqual(split_entry_markdown(None), [("markdown", "")])

    def test_image_only_paragraph_becomes_image_segment(self):
        text = "# Title\n\nBody text.\n\n![logo](/log/attachments/attachment.1.png)"
        segments = split_entry_markdown(text)
        self.assertEqual(segments[-1], ("image", "attachment.1.png", "logo"))
        self.assertEqual(segments[0], ("markdown", "# Title\n\nBody text.\n\n"))

    def test_mixed_text_and_image_paragraph_stays_markdown(self):
        text = "Text with an ![inline](/log/attachments/a.png) image inside."
        self.assertEqual(split_entry_markdown(text), [("markdown", text)])

    def test_two_images_in_one_paragraph_become_two_segments(self):
        text = "![a](/log/attachments/a.png)\n![b](/log/attachments/b.png)\n"
        segments = split_entry_markdown(text)
        self.assertEqual(
            segments, [("image", "a.png", "a"), ("image", "b.png", "b")])

    def test_image_paragraph_surrounded_by_text(self):
        text = "Before\n\n![a](/log/attachments/a.png)\n\nAfter"
        segments = split_entry_markdown(text)
        self.assertEqual(segments, [
            ("markdown", "Before\n\n"),
            ("image", "a.png", "a"),
            ("markdown", "\nAfter"),
        ])

    def test_pdf_attachment_paragraph_stays_markdown(self):
        text = "See [report](/api/Downloads/Attachments/report.pdf) attached."
        self.assertEqual(split_entry_markdown(text), [("markdown", text)])

    def test_external_image_url_stays_markdown(self):
        text = "![ext](https://example.com/x.png)"
        self.assertEqual(split_entry_markdown(text), [("markdown", text)])

    def test_api_downloads_prefix_recognized(self):
        text = "![a](/api/Downloads/Attachments/a.png)"
        self.assertEqual(split_entry_markdown(text), [("image", "a.png", "a")])


if __name__ == "__main__":
    unittest.main()
