import telegram
import logging
import schedule
import time
from datetime import date
import json
from params import bottoken
bot = telegram.Bot(token=bottoken)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

target = '@edailymanna'


def link(ref):
    ref = '<a href="https://www.biblegateway.com/passage/?search={}&version=KJV">{}</a>'.format(
        ref, ref)
    return ref


def command():
    try:
        with open('quarter.json') as datafile:
            data = json.load(datafile)
        today = date.today().strftime("%e %B").strip().upper()
        payload = data[today]
        full = '<b><u>{}</u></b>'.format(today)
        full += '\n\n<b>BIBLE LESSON</b>\n' + link(payload['part1'])
        full += '\n\n<b>LESSON</b>\n' + payload['part2']
        full += '\n\n<b>{}</b>\n<i>{}</i>'.format(
            payload['part3'], payload['part4'])
        full += '\n\n' + payload['part5']
        full += '\n\n<b>{}</b>\n{}'.format(payload['part6'], payload['part7'])
        full += '\n\n<i>TO COMPLETE THE BIBLE IN 2 YEARS, READ</i><b>'
        for verse in payload['part8']:
            full += '\n' + link(verse)
        full += '</b>'
        bot.send_message(chat_id=target, text=full,
                         parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    except:
        bot.send_message(chat_id=target, text="_We are facing technical difficulties and are unable to send today's devotion_",
                         parse_mode=telegram.ParseMode.MARKDOWN, disable_notification=True)


def main():
    schedule.every().day.at("06:00").do(command)
    print("Bot running: task scheduled.")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    main()
