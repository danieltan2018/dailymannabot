import json
import pdftotext
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from datetime import timedelta, date
from unidecode import unidecode
import threading

rawtext = {}
ocrtext = {}
dates = []


def daterange(date1, date2):
    for n in range(int((date2 - date1).days)+1):
        yield date1 + timedelta(n)


start_dt = date(2022, 10, 1)
end_dt = date(2022, 12, 31)
for dt in daterange(start_dt, end_dt):
    dt_str = dt.strftime("%e %B").strip().upper()
    dates.append(dt_str)

filename = 'd.pdf'

with open(filename, "rb") as f:
    pdf = pdftotext.PDF(f)

i = 0
for page in pdf:
    key = dates[i]
    rawtext[key] = str(page)
    i += 1

pages = convert_from_path(filename, 500, thread_count=100)


def ocr(key, img):
    global ocrtext
    ocrtext[key] = str(pytesseract.image_to_string(img))


threads = []
for i in range(len(pages)):
    t = threading.Thread(target=ocr, args=[dates[i], pages[i]])
    t.start()
    threads.append(t)

for thread in threads:
    thread.join()

quarter = {}

for x in dates:
    rawpage = rawtext[x]
    rawlines = rawpage.split('\n')
    indent = len(rawlines[0]) - len(rawlines[0].lstrip(' '))
    linenum = 1
    verse = ''
    devotion = ''
    ending = ''
    continued = True
    for line in rawlines:
        otherline = line[:indent]
        otherline = otherline.strip()
        if len(otherline) > 7:
            verse += otherline + ' '
        line = line[indent:]
        if linenum < 3:
            dropcap = line[0]
            line = line[1:]
            line = line.strip()
            if dropcap != ' ':
                line = dropcap + line
        newpara = False
        if line.startswith('    '):
            newpara = True
        line = line.strip()

        if line == '':
            continued = False
        if newpara and continued:
            devotion += '\n\n' + line
        elif continued:
            devotion += ' ' + line
        else:
            ending += line + ' '
        linenum += 1
    verse = verse.strip()
    devotion = devotion.strip()
    ending = ending.strip()

    ocrpage = ocrtext[x]
    ocrlines = ocrpage.split('\n')
    position = 0
    biblelesson = ''
    lesson = ''
    verseref = ''
    read = []
    endingtype = ''
    for line in ocrlines:
        line = line.strip()
        if line == 'BIBLE LESSON':
            position = 1
        elif line == 'LESSON':
            position = 2
        elif line.startswith('VERSE '):
            position = 3
            verseref = line
        elif line == 'To CompeLETE THE BIBLE':
            position = 4
        elif line == 'IN 2 YEARS, READ':
            position = 5
        elif line == 'PRAYER' or line == 'THOUGHT' or line == 'CHALLENGE' or line == 'MEDITATION':
            endingtype = line
            break
        else:
            if position == 1:
                biblelesson += line
            elif position == 2:
                lesson += line + ' '
            elif position == 5 and line:
                read.append(unidecode(line).strip())

    payload = {}
    payload['part1'] = unidecode(biblelesson).strip()
    payload['part2'] = unidecode(lesson).strip()
    payload['part3'] = unidecode(verseref).strip()
    payload['part4'] = unidecode(verse).strip()
    payload['part5'] = unidecode(devotion).strip()
    payload['part6'] = unidecode(endingtype).strip()
    payload['part7'] = unidecode(ending).strip()
    payload['part8'] = read
    quarter[x] = payload

data = json.dumps(quarter)
with open("quarter_new.json", "w") as f:
    f.write(data)
