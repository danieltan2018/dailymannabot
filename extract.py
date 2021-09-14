import json
import pdftotext
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from datetime import timedelta, date
from unidecode import unidecode

rawtext = []
ocrtext = []
dates = []

filename = 'd.pdf'

with open(filename, "rb") as f:
    pdf = pdftotext.PDF(f)

for page in pdf:
    rawtext.append(str(page))

pages = convert_from_path(
    filename, dpi=500, output_folder='convert', thread_count=100)

for page in pages:
    ocrtext.append(str(pytesseract.image_to_string(page)))


def daterange(date1, date2):
    for n in range(int((date2 - date1).days)+1):
        yield date1 + timedelta(n)


start_dt = date(2021, 7, 1)
end_dt = date(2021, 9, 30)
for dt in daterange(start_dt, end_dt):
    dates.append(dt)

quarter = {}

for x in range(len(rawtext)):
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

    today = dates[x].strftime("%e %B").strip().upper()
    payload = {}
    payload['part1'] = unidecode(biblelesson).strip()
    payload['part2'] = unidecode(lesson).strip()
    payload['part3'] = unidecode(verseref).strip()
    payload['part4'] = unidecode(verse).strip()
    payload['part5'] = unidecode(devotion).strip()
    payload['part6'] = unidecode(endingtype).strip()
    payload['part7'] = unidecode(ending).strip()
    payload['part8'] = read
    quarter[today] = payload

data = json.dumps(quarter)
with open("quarter_new.json", "w") as f:
    f.write(data)
