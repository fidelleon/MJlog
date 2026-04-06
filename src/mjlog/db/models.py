"""SQLAlchemy data models."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

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
