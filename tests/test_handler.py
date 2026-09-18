import unittest
from unittest import mock

import handler

FAKE_RESULT = {"ok": True, "result": {"message_id": 7, "chat": {"id": -100, "username": "thruthepsalms"}}}


class HandlerTest(unittest.TestCase):
    @mock.patch("handler.telegram.send_message", return_value=FAKE_RESULT)
    def test_sends_requested_day_to_channel(self, send):
        out = handler.lambda_handler({"channel": "psalms", "date": "2024-05-02"}, None)
        chat_id, text = send.call_args.args
        self.assertEqual(chat_id, "@thruthepsalms")
        self.assertTrue(text.startswith("<u>2 MAY</u>"))
        self.assertEqual(out["date"], "2 MAY")
        self.assertEqual(out["message_id"], 7)

    @mock.patch("handler.telegram.send_message", return_value=FAKE_RESULT)
    def test_chat_id_override_for_manual_testing(self, send):
        handler.lambda_handler({"channel": "psalms", "chat_id": "@mytest"}, None)
        self.assertEqual(send.call_args.args[0], "@mytest")

    def test_unknown_channel_raises(self):
        with self.assertRaises(ValueError):
            handler.lambda_handler({"channel": "nope"}, None)
        with self.assertRaises(ValueError):
            handler.lambda_handler({}, None)

    @mock.patch("handler.telegram.send_message")
    @mock.patch("channels.Channel.load_data", return_value={})
    def test_missing_date_raises_before_sending(self, load_data, send):
        with self.assertRaises(KeyError):
            handler.lambda_handler({"channel": "psalms", "date": "2024-05-02"}, None)
        send.assert_not_called()
