"""Checks specific to the Our Daily Walk data shape and renderer."""

import unittest

from channels import CHANNELS
from renderers import our_daily_walk


class OurDailyWalkDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = CHANNELS["our_daily_walk"].load_data()

    def test_scripture_lines_are_quoted(self):
        for key, entry in self.data.items():
            for line in entry["scripture"].split("\n"):
                with self.subTest(day=key):
                    self.assertTrue(line.startswith("“") and line.endswith("”"), line[:40])

    def test_titles_are_upper_case_as_printed(self):
        for key, entry in self.data.items():
            with self.subTest(day=key):
                self.assertEqual(entry["title"], entry["title"].upper())

    def test_almost_every_day_ends_with_a_prayer(self):
        # Three days end with a short poem instead (as printed).
        without = {k for k, e in self.data.items() if not e["text"].split("\n\n")[-1].startswith("PRAYER")}
        self.assertEqual(without, {"23 JANUARY", "28 JANUARY", "27 MAY"})


class OurDailyWalkRenderTest(unittest.TestCase):
    def test_layout(self):
        entry = {
            "title": "A TITLE",
            "reference": "John 3:16; Psalm 23",
            "scripture": "“First.”\n“Second.”",
            "text": "Body one.\n\nBody two.\n\nPRAYER—Amen.",
        }
        out = our_daily_walk.render("1 JANUARY", entry)
        self.assertEqual(
            out.split("\n"),
            [
                "<u>1 JANUARY</u>",
                "",
                "<b>A TITLE</b>",
                "",
                "<i>“First.”</i>",
                "<i>“Second.”</i>",
                '— <a href="https://www.biblegateway.com/passage/?search=John+3%3A16%3B+Psalm+23&version=KJV">John 3:16; Psalm 23</a>',
                "",
                "Body one.",
                "",
                "Body two.",
                "",
                "<i>PRAYER—Amen.</i>",
            ],
        )
