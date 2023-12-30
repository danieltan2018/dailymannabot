import telegram
import logging
import schedule
import time
from datetime import date
import json
from params import bottoken

bot = telegram.Bot(token=bottoken)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

target = "@thruthepsalms"


def link(ref):
    ref = '<a href="https://www.biblegateway.com/passage/?search={}&version=KJV">{}</a>'.format(
        ref, ref
    )
    return ref


def command():
    try:
        with open("psalms.json") as datafile:
            data = json.load(datafile)
        today = date.today().strftime("%e %B").strip().upper()
        payload = data[today]
        full = "<u>{}</u>".format(today)
        full += "\n\n<b>{}</b>".format(link(payload["psalm"]))
        full += "\n<b>{}</b>".format(payload["title"])
        full += "\n\n<i>{}</i>".format(payload["verse"])
        full += "\n\n" + payload["text"]
        bot.send_message(
            chat_id=target,
            text=full,
            parse_mode=telegram.ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except:
        bot.send_message(
            chat_id=target,
            text="_We are facing technical difficulties and are unable to send today's devotion_",
            parse_mode=telegram.ParseMode.MARKDOWN,
            disable_notification=True,
        )


def main():
    schedule.every().day.at("06:00").do(command)
    print("Bot running: task scheduled.")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
