"""SQLAlchemy data models."""
import csv
import datetime
import enum
import io
import re
import zipfile

import feedparser
import requests
from bs4 import BeautifulSoup

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

from mjlog.db.session import get_session

Base = declarative_base()


class DXCCEntity(Base):
    """DXCC (DX Century Club) entity model from external_data/DXCC.xlsx.

    Represents a ham radio country/entity with prefix, zone, coordinates, etc.
    Data source: http://www.arrl.org/dxcc/

    Uniqueness enforced on (prefix, entity_code, special_use) composite key.
    """

    __tablename__ = "dxcc_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prefix = Column(String(20), nullable=False, index=True)
    dxcc_name = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    continent = Column(String(2), nullable=False)
    itu_zone = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    utc_offset = Column(Integer, nullable=True)
    prefixes = Column(String(100000), nullable=True)
    cq_zone_id = Column(Integer, nullable=True)
    entity_code = Column(Integer, nullable=False)
    special_use = Column(Boolean, default=False, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'prefix', 'entity_code', 'special_use',
            name='uq_dxcc_prefix_code_special'
        ),
    )

    def __repr__(self):
        return (
            f"<DXCCEntity(prefix='{self.prefix}', "
            f"name='{self.name}', continent='{self.continent}')>"
        )

    @staticmethod
    def get_big_cty():
        """Fetch the latest Big CTY data and update database prefixes."""
        # Use country-files feed to find the latest Big CTY URL
        date_matcher = re.compile(r'^.*?\s(\d\d)\s.*?(\w+)\s(\d+)')
        url: str = "https://www.country-files.com/feed/"
        feed = feedparser.parse(url)
        if feed.status != 200:
            raise Exception(f"Failed to fetch feed: HTTP {feed.status}")

        bigcty_data: dict | None = next(
            (entry for entry in feed.entries if entry.title.startswith('Big CTY')),
            None,
        )
        if bigcty_data is None:
            raise Exception("Big CTY entry not found in feed")

        title = bigcty_data['title']
        # This is not a regular dash, but an en dash (U+2013).
        filename = title.split(' – ')[0]

        matcher = date_matcher.match(title)
        if not matcher:
            raise Exception(f"Failed to parse date from title: {title}")

        groups = matcher.groups()

        # Format is "Big CTY – 22 October 2024".
        file_date: datetime.date = datetime.date(
            int(groups[2]),
            datetime.datetime.strptime(groups[1], '%B').month,
            int(groups[0]),
        )
        bigcty_url: str = bigcty_data['link']

        # Now, request the Big CTY page to find the actual download link
        response = requests.get(bigcty_url)
        response.raise_for_status()  # Ensure we got a successful response
        soup = BeautifulSoup(response.content, "html.parser")
        tag = soup.find('a', text='[download]')
        if tag is None:
            raise Exception("Download link not found in Big CTY page")

        # Now we have the download link, let's fetch the zip file
        bigcty_response = requests.get(tag['href'])
        bigcty_response.raise_for_status()
        buffer = io.BytesIO(bigcty_response.content)

        with zipfile.ZipFile(buffer, 'r') as zf:
            csv_data = zf.read("cty.csv")

        csv_file = csv.reader(io.StringIO(csv_data.decode('utf-8')))
        session = get_session()

        rows = [line for line in csv_file if len(line) > CtyLine.prefixes.value]
        cty_names = {line[CtyLine.name.value] for line in rows}
        entities_by_name = {}
        if cty_names:
            entities_by_name = {
                entity.name: entity
                for entity in session.query(DXCCEntity)
                .filter(DXCCEntity.name.in_(cty_names))
                .all()
            }

        for line in rows:
            cty_name = line[CtyLine.name.value]
            entity = entities_by_name.get(cty_name)
            if entity:
                entity.prefixes = line[CtyLine.prefixes.value].rstrip(';')
            else:
                print(f"Warning: No matching DXCCEntity found for {cty_name}")

        today = datetime.date.today()
        version = file_date.isoformat()
        updated = (
            session.query(InternetImportation)
            .filter(InternetImportation.filename == filename)
            .update(
                {
                    InternetImportation.import_date: today,
                    InternetImportation.import_version: version,
                },
                synchronize_session=False,
            )
        )

        if not updated:
            importation = InternetImportation(
                filename=filename,
                import_date=today,
                import_version=version
            )
            session.add(importation)
        session.commit()


class InternetImportation(Base):
    """Internet importation record for tracking data synchronization."""

    __tablename__ = "internet_importations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(32), nullable=False)
    import_version = Column(String(32), nullable=True)
    import_date = Column(Date, nullable=False)

    def __repr__(self):
        return (
            f"<InternetImportation(filename='{self.filename}', "
            f"import_date='{self.import_date}')>"
        )


class Band(Base):
    """Band configuration record."""

    __tablename__ = "bands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    band = Column(String, nullable=True)
    enabled = Column(String, nullable=True)
    minfreqr1 = Column(Numeric, nullable=True)
    maxfreqr1 = Column(Numeric, nullable=True)
    minfreqr2 = Column(Numeric, nullable=True)
    maxfreqr2 = Column(Numeric, nullable=True)
    minfreqr3 = Column(Numeric, nullable=True)
    maxfreqr3 = Column(Numeric, nullable=True)
    sat_mode = Column(String, nullable=True)

    def __repr__(self):
        return (
            f"<Band(id={self.id}, band='{self.band}', enabled='{self.enabled}')>"
        )


class Mode(Base):
    """Radio mode record.

    Represents ham radio transmission modes such as FM, CW, SSB, FT8, etc.
    Data source: external_data/modes.csv
    """

    __tablename__ = "modes"

    mode = Column(String(20), primary_key=True, nullable=False, index=True, unique=True)
    submode = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<Mode(mode='{self.mode}', submode='{self.submode}')>"


class Submode(Base):
    """Submode record linked to a Mode.

    Represents specific submodes associated with a radio transmission mode.
    Each submode record must reference a valid Mode.
    """

    __tablename__ = "submodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(String(20), ForeignKey('modes.mode'), nullable=False, index=True)
    submode = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<Submode(mode='{self.mode}', submode='{self.submode}')>"


class ModesByFrequency(Base):
    """Frequency range record for radio modes.

    Represents the frequency ranges (in kHz) where each mode is active.
    Data source: external_data/modes_by_frequency.csv
    """

    __tablename__ = "modes_by_frequency"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(String(20), nullable=False, index=True)
    minfrequency = Column(Float, nullable=False)
    maxfrequency = Column(Float, nullable=False)

    def __repr__(self):
        return f"<ModesByFrequency(mode='{self.mode}', {self.minfrequency}-{self.maxfrequency} kHz)>"


class Station(Base):
    """Amateur radio station record.

    Represents an amateur radio station with callsign, location, and operational details.
    Data source: external_data/stations.csv

    Constraints:
    - Either (latitude AND longitude) OR locator must be provided
    - If both active_from and active_to are provided, active_from <= active_to
    """

    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String(255), nullable=False)
    callsign = Column(String(32), nullable=False, unique=True, index=True)
    operators = Column(String(255), nullable=False)
    callsigns = Column(String(255), nullable=True)
    location = Column(String(255), nullable=False)
    utc_difference = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    locator = Column(String(10), nullable=True)
    lotw_user = Column(String(32), nullable=True)
    lotw_callsign = Column(String(32), nullable=True)
    eqsl_user = Column(String(32), nullable=True)
    eqsl_nickname = Column(String(32), nullable=True)
    active_from = Column(Date, nullable=True)
    active_to = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(
            '(latitude IS NOT NULL AND longitude IS NOT NULL) OR locator IS NOT NULL',
            name='ck_station_location'
        ),
        CheckConstraint(
            'active_from IS NULL OR active_to IS NULL OR active_from <= active_to',
            name='ck_station_active_dates'
        ),
    )

    def __repr__(self):
        return f"<Station(callsign='{self.callsign}', name='{self.station_name}')>"


class Membership(Base):
    """LoTW membership record for amateur radio callsigns.

    Tracks LoTW (Logbook of The World) membership information.
    Data source: external_data/membership.csv

    Constraints:
    - If lotw_time is provided, lotw_date becomes mandatory
    """

    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    callsign = Column(String(32), nullable=False, unique=True, index=True)
    lotw_date = Column(Date, nullable=True)
    lotw_time = Column(Time, nullable=True)

    __table_args__ = (
        CheckConstraint(
            'lotw_time IS NULL OR lotw_date IS NOT NULL',
            name='ck_membership_time_requires_date'
        ),
    )

    def __repr__(self):
        return f"<Membership(callsign='{self.callsign}')>"


class CacheEntry(Base):
    """Generic key-value cache store backed by PostgreSQL.

    Supports namespaced entries with TTL-based expiry.
    Used for caching external API responses such as QRZ session keys and
    callsign lookups to reduce round-trips to remote services.

    Uniqueness is enforced on (namespace, key).
    """

    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    namespace = Column(String(64), nullable=False, index=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint('namespace', 'key', name='uq_cache_namespace_key'),
    )

    def __repr__(self):
        return (
            f"<CacheEntry(namespace='{self.namespace}', key='{self.key}', "
            f"expires_at={self.expires_at})>"
        )

    def is_expired(self) -> bool:
        """Return True if this cache entry has passed its TTL."""
        if self.expires_at is None:
            return False
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at


class HRDQso(Base):
    """Read-only mapping to remote HRD MySQL QSO (contact) log table.

    This model provides read-only access to the Ham Radio Deluxe (HRD) QSO
    database at 192.168.1.177:3306/hrd.table_hrd_contacts_v07.

    The table contains comprehensive QSO logging with 198 columns including:
    - Core QSO data: date, time, callsign, frequency, mode, RST
    - Location: coordinates, grid square, DXCC entity
    - QSL info: LoTW, eQSL, direct QSL tracking
    - Station data: operator, rig, antenna configuration
    - Contest info: contest ID, exchange received/sent
    - Special awards: SOTA, POTA, IOTA, WWFF, USACA counties

    Note: This is a read-only model. Use case-insensitive queries for HRD
    columns which use ALL_CAPS naming convention (e.g., COL_CALL, COL_QSO_DATE).

    Connection: MySQL at 192.168.1.177:3306/hrd (username: hrd, password: hrd)
    Primary key: COL_PRIMARY_KEY (BIGINT)
    Last synced: table_hrd_contacts_v07
    """

    __tablename__ = "table_hrd_contacts_v07"

    # Primary key
    primary_key = Column('COL_PRIMARY_KEY', Integer, primary_key=True)

    # Core QSO data
    qso_date = Column('COL_QSO_DATE', Date, index=True)
    time_on = Column('COL_TIME_ON', Time)
    time_off = Column('COL_TIME_OFF', Time)
    call = Column('COL_CALL', String(32), index=True)
    freq = Column('COL_FREQ', Integer)
    freq_rx = Column('COL_FREQ_RX', Integer)
    mode = Column('COL_MODE', String(16), index=True)
    band = Column('COL_BAND', String(10), index=True)
    submode = Column('COL_SUBMODE', String(16))
    rst_sent = Column('COL_RST_SENT', String(32))
    rst_rcvd = Column('COL_RST_RCVD', String(32))
    tx_pwr = Column('COL_TX_PWR', Float)
    rx_pwr = Column('COL_RX_PWR', Float)

    # Location data
    lat = Column('COL_LAT', Float)
    lon = Column('COL_LON', Float)
    my_lat = Column('COL_MY_LAT', Float)
    my_lon = Column('COL_MY_LON', Float)
    gridsquare = Column('COL_GRIDSQUARE', String(12), index=True)
    my_gridsquare = Column('COL_MY_GRIDSQUARE', String(12))
    qth = Column('COL_QTH', String(255))
    my_city = Column('COL_MY_CITY', String(32))
    my_state = Column('COL_MY_STATE', String(32))
    state = Column('COL_STATE', String(32), index=True)

    # DXCC/Zone data
    dxcc = Column('COL_DXCC', String(6), index=True)
    my_dxcc = Column('COL_MY_DXCC', String(6))
    country = Column('COL_COUNTRY', String(255), index=True)
    my_country = Column('COL_MY_COUNTRY', String(255))
    cqz = Column('COL_CQZ', Integer, index=True)
    my_cq_zone = Column('COL_MY_CQ_ZONE', Integer)
    ituz = Column('COL_ITUZ', Integer, index=True)
    my_itu_zone = Column('COL_MY_ITU_ZONE', Integer)
    cont = Column('COL_CONT', String(6), index=True)

    # Station identifiers
    station_callsign = Column('COL_STATION_CALLSIGN', String(32), index=True)
    operator = Column('COL_OPERATOR', String(255))
    contacted_op = Column('COL_CONTACTED_OP', String(32))
    name = Column('COL_NAME', String(255))

    # QSL tracking
    qsl_sent = Column('COL_QSL_SENT', String(2))
    qsl_rcvd = Column('COL_QSL_RCVD', String(2))
    qsl_sent_via = Column('COL_QSL_SENT_VIA', String(2))
    qsl_rcvd_via = Column('COL_QSL_RCVD_VIA', String(2))
    qslsdate = Column('COL_QSLSDATE', Date)
    qslrdate = Column('COL_QSLRDATE', Date)

    # LoTW tracking
    lotw_qsl_sent = Column('COL_LOTW_QSL_SENT', String(2))
    lotw_qsl_rcvd = Column('COL_LOTW_QSL_RCVD', String(2))
    lotw_qslsdate = Column('COL_LOTW_QSLSDATE', Date)
    lotw_qslrdate = Column('COL_LOTW_QSLRDATE', Date)

    # eQSL tracking
    eqsl_qsl_sent = Column('COL_EQSL_QSL_SENT', String(2))
    eqsl_qsl_rcvd = Column('COL_EQSL_QSL_RCVD', String(2))
    eqsl_qslsdate = Column('COL_EQSL_QSLSDATE', Date)
    eqsl_qslrdate = Column('COL_EQSL_QSLRDATE', Date)

    # Contest data
    contest_id = Column('COL_CONTEST_ID', String(32))
    stx = Column('COL_STX', Integer)
    stx_string = Column('COL_STX_STRING', String(32))
    srx = Column('COL_SRX', Integer)
    srx_string = Column('COL_SRX_STRING', String(32))
    check = Column('COL_CHECK', String(8))
    precedence = Column('COL_PRECEDENCE', String(255))

    # Special awards
    iota = Column('COL_IOTA', String(10), index=True)
    iota_island_id = Column('COL_IOTA_ISLAND_ID', Integer)
    my_iota = Column('COL_MY_IOTA', String(10))
    sota_ref = Column('COL_SOTA_REF', String(255))
    my_sota_ref = Column('COL_MY_SOTA_REF', String(32))
    wwff_ref = Column('COL_WWFF_REF', String(255))
    my_wwff_ref = Column('COL_MY_WWFF_REF', String(32))
    pota_ref = Column('COL_POTA_REF', String(255))
    my_pota_ref = Column('COL_MY_POTA_REF', String(255))
    usaca_counties = Column('COL_USACA_COUNTIES', String(255))

    # Notes
    comment = Column('COL_COMMENT', String(255))
    notes = Column('COL_NOTES', String(255))

    # Propagation
    prop_mode = Column('COL_PROP_MODE', String(8))
    sfi = Column('COL_SFI', Integer)
    k_index = Column('COL_K_INDEX', Integer)
    a_index = Column('COL_A_INDEX', Float)
    max_bursts = Column('COL_MAX_BURSTS', Integer)
    nr_bursts = Column('COL_NR_BURSTS', Integer)
    nr_pings = Column('COL_NR_PINGS', Integer)
    ms_shower = Column('COL_MS_SHOWER', String(32))

    # Equipment
    rig = Column('COL_RIG', String(255))
    my_rig = Column('COL_MY_RIG', String(255))
    ant_az = Column('COL_ANT_AZ', Float)
    ant_el = Column('COL_ANT_EL', Float)

    def __repr__(self):
        """Represent HRDQso record with QSO date, time, and callsign."""
        date_str = self.qso_date.isoformat() if self.qso_date else 'None'
        time_str = self.time_on.isoformat() if self.time_on else 'None'
        return (
            f"<HRDQso(date={date_str}, time={time_str}, "
            f"call='{self.call}', band={self.band}, "
            f"mode='{self.mode}')>"
        )

    @staticmethod
    def get_hrd_qsos():
        """Fetch all QSOs from the HRD database."""
        session = get_session(db="hrd")
        return session.query(HRDQso).filter(HRDQso.call == 'CT3MD').all()


class CtyLine(enum.Enum):
    """Enum for column indices in cty.csv from Big CTY."""
    # Example row:
    # ['XX9', 'Macao', '152', 'AS', '24', '44',
    #  '22.10', '-113.50', '-8.0', 'XX9;']
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
