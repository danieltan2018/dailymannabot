"""Checks specific to the Psalms data shape and renderer."""

import re
import unittest

from channels import CHANNELS
from renderers import bible_link, psalms

PSALM_REF = re.compile(r"^Psalm \d{1,3}(:\d+(-\d+)?)?(-\d{1,3})?$")
VERSE_CITATION = re.compile(r"\(Psalm \d{1,3}:[\d\-, ;:]+\)$")


class PsalmsDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = CHANNELS["psalms"].load_data()

    def test_psalm_reference_format(self):
        for key, entry in self.data.items():
            with self.subTest(day=key):
                self.assertRegex(entry["psalm"], PSALM_REF)

    def test_verse_ends_with_citation(self):
        for key, entry in self.data.items():
            with self.subTest(day=key):
                self.assertRegex(entry["verse"], VERSE_CITATION)


class PsalmsRenderTest(unittest.TestCase):
    def test_html_special_characters_are_escaped(self):
        entry = {"psalm": "Psalm 1", "title": "A & B", "verse": "<v>", "text": "x < y"}
        message = psalms.render("1 JANUARY", entry)
        self.assertIn("A &amp; B", message)
        self.assertIn("&lt;v&gt;", message)
        self.assertIn("x &lt; y", message)

    def test_link_url_encodes_reference(self):
        self.assertIn("search=Psalm+54%3A1-7&version=KJV", bible_link("Psalm 54:1-7"))
