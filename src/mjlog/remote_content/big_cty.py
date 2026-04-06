import csv
import enum
import io
import sys
import zipfile
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mjlog.db.models import DXCCEntity
from mjlog.db.session import get_session


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

def get_big_cty():
    """Fetches the big_cty.txt file from the ARRL website and returns a list of lines."""
    # Use country-files feed to find the latest Big CTY URL
    url: str = "https://www.country-files.com/feed/"
    feed = feedparser.parse(url)
    if feed.status != 200:
        raise Exception(f"Failed to fetch feed: HTTP {feed.status}")
    bigcty_data: dict| None = next((entry for entry in feed.entries if entry.title.startswith('Big CTY')), None)
    if bigcty_data is None:
        raise Exception("Big CTY entry not found in feed")
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
            entity.prefixes = line[CtyLine.prefixes.value]
        else:
            print(f"Warning: No matching DXCCEntity found for {cty_name}")

    session.commit()

