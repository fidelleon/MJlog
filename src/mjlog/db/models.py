"""SQLAlchemy data models."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
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
