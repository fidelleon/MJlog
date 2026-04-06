"""Data loaders for importing external data into database."""
import csv
import datetime
import enum
import io
import re
import zipfile

import feedparser
import requests
from bs4 import BeautifulSoup

from mjlog.db.models import DXCCEntity
from mjlog.db.session import get_session

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def col_letter_to_num(col_letter):
    """Convert Excel column letter to 0-based position (A=0, B=1, ..., Z=25, AA=26)."""
    result = 0
    for char in col_letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1

def get_big_cty():
    """Fetches the big_cty.txt file from the ARRL website and returns a list of lines."""
    # Use country-files feed to find the latest Big CTY URL
    date_matcher = re.compile(r'^.*?\s(\d\d)\s.*?(\w+)\s(\d+)')
    url: str = "https://www.country-files.com/feed/"
    feed = feedparser.parse(url)
    if feed.status != 200:
        raise Exception(f"Failed to fetch feed: HTTP {feed.status}")
    bigcty_data: dict| None = next((entry for entry in feed.entries if entry.title.startswith('Big CTY')), None)
    if bigcty_data is None:
        raise Exception("Big CTY entry not found in feed")
    title = bigcty_data['title']
    filename = title.split(' – ')[0]  # This is not a regular dash, but an en dash (U+2013)
    print(filename)
    matcher = date_matcher.match(title)
    if not matcher:
        raise Exception(f"Failed to parse date from title: {title}")

    groups = matcher.groups()
    file_date = datetime.date(int(groups[2]), datetime.datetime.strptime(groups[1], '%B').month, int(groups[0]))
    return file_date
    bigcty_url: str = bigcty_data['link']

    # Now, request the Big CTY page to find the actual download link
    response = requests.get(bigcty_url)
    response.raise_for_status()  # Ensure we got a successful response
    soup = BeautifulSoup(response.content, "html.parser")
    tag = soup.find('a', text='[download]')
    if tag is None:
        raise Exception("Download link not found in Big CTY page")

    # Now we hve the download link, let's fetch the zip file
    bigcty_response = requests.get(tag['href'])
    bigcty_response.raise_for_status()
    buffer = io.BytesIO(bigcty_response.content)

    with zipfile.ZipFile(buffer, 'r') as zf:
        csv_data = zf.read("cty.csv")

    csv_file = csv.reader(io.StringIO(csv_data.decode('utf-8')))
    session = get_session()

    for line in csv_file:
        cty_name = line[CtyLine.name.value]
        # Query for DXCCEntity matching the cty_name
        entity = session.query(DXCCEntity).filter(DXCCEntity.name == cty_name).first()
        if entity:
            entity.prefixes = line[CtyLine.prefixes.value][:-1]  # Remove trailing ';'
        else:
            print(f"Warning: No matching DXCCEntity found for {cty_name}")

    session.commit()


class CtyLine(enum.Enum):
    """Enum for column indices in cty.csv from Big CTY."""
    # ['XX9', 'Macao', '152', 'AS', '24', '44', '22.10', '-113.50', '-8.0', 'XX9;']
    prefix = 0
    name = 1
    entity_code = 2
    continent = 3
    cq_zone_id = 4
    itu_zone = 5
    latitude = 6
    longitude = 7
    utc_offset = 8
    prefixes = 9
