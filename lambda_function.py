import os
import requests
from datetime import date
from datetime import timedelta
import urllib.parse
import json

TOKEN = os.environ.get("BOT_TOKEN")
TARGET = "@thruthepsalms"


def link(ref):
    return '<a href="https://www.biblegateway.com/passage/?search={}&version=KJV">{}</a>'.format(
        ref, ref
    )


def lambda_handler(event, context):
    with open("psalms.json") as datafile:
        data = json.load(datafile)
    today = date.today() + timedelta(days=1)
    today = today.strftime("%e %B").strip().upper()
    payload = data[today]
    full = "<u>{}</u>".format(today)
    full += "\n\n<b>{}</b>".format(link(payload["psalm"]))
    full += "\n<b>{}</b>".format(payload["title"])
    full += "\n\n<i>{}</i>".format(payload["verse"])
    full += "\n\n" + payload["text"]
    TEXT = urllib.parse.quote(full)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={TARGET}&text={TEXT}&parse_mode=html&disable_web_page_preview=true"
    return {"statusCode": 200, "body": requests.get(url).json()}
