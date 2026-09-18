"""Generic checks that every registered channel's data file is complete and clean.

Run with:  python3 -m unittest
"""

import re
import unittest
from datetime import date, timedelta

from channels import CHANNELS, date_key
from telegram import TELEGRAM_MAX_LENGTH


def every_day_of_a_leap_year():
    start = date(2024, 1, 1)
    return [start + timedelta(days=n) for n in range(366)]


class ChannelDataTest(unittest.TestCase):
    """Runs every check against every channel in the registry."""

    @classmethod
    def setUpClass(cls):
        cls.data = {name: channel.load_data() for name, channel in CHANNELS.items()}

    def test_every_day_of_the_year_has_an_entry(self):
        expected = {date_key(d) for d in every_day_of_a_leap_year()}
        for name, data in self.data.items():
            with self.subTest(channel=name):
                self.assertEqual(set(data), expected)

    def test_entries_have_exactly_the_renderers_fields(self):
        for name, data in self.data.items():
            for key, entry in data.items():
                with self.subTest(channel=name, day=key):
                    self.assertEqual(set(entry), CHANNELS[name].renderer.FIELDS)

    def test_fields_are_clean_text(self):
        for name, data in self.data.items():
            for key, entry in data.items():
                for field, value in entry.items():
                    with self.subTest(channel=name, day=key, field=field):
                        self.assertTrue(value, "empty")
                        self.assertEqual(value, value.strip(), "leading/trailing whitespace")
                        self.assertNotIn("  ", value, "double space")
                        self.assertIsNone(re.search(r"\w- \w", value), "line-wrap hyphenation")

    def test_rendered_messages_fit_telegram_limit(self):
        for name, data in self.data.items():
            for key, entry in data.items():
                with self.subTest(channel=name, day=key):
                    self.assertLess(len(CHANNELS[name].render(key, entry)), TELEGRAM_MAX_LENGTH)


class DateKeyTest(unittest.TestCase):
    def test_no_zero_padding(self):
        self.assertEqual(date_key(date(2024, 5, 2)), "2 MAY")
        self.assertEqual(date_key(date(2024, 12, 31)), "31 DECEMBER")
