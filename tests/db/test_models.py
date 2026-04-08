"""Tests for mjlog.db.models module."""

import pytest
from datetime import date, time

from mjlog.db.models import Mode, Submode, Station, Membership, ModesByFrequency


class TestMode:
    """Test Mode model."""

    def test_mode_creation(self, db_session):
        """Test creating a Mode record in the database.
        
        Verifies that a Mode can be created with a unique mode name
        and optional submode.
        
        Args:
            db_session: Database session fixture.
        """
        mode = Mode(mode="FT8", submode="FT4")
        db_session.add(mode)
        db_session.commit()

        retrieved = db_session.query(Mode).filter_by(mode="FT8").first()
        assert retrieved is not None
        assert retrieved.mode == "FT8"
        assert retrieved.submode == "FT4"

    def test_mode_unique_constraint(self, db_session):
        """Test that mode field enforces uniqueness constraint.
        
        Verifies that creating two Mode records with the same mode name
        raises an integrity error.
        
        Args:
            db_session: Database session fixture.
        """
        mode1 = Mode(mode="SSB")
        db_session.add(mode1)
        db_session.commit()

        mode2 = Mode(mode="SSB")
        db_session.add(mode2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_mode_repr(self):
        """Test Mode __repr__ method.
        
        Verifies that the string representation of a Mode object
        is formatted correctly.
        """
        mode = Mode(mode="CW", submode="PCW")
        assert "<Mode(mode='CW', submode='PCW')>" in repr(mode)

    def test_mode_submode_optional(self, db_session):
        """Test that submode field is optional.
        
        Verifies that a Mode can be created without a submode.
        
        Args:
            db_session: Database session fixture.
        """
        mode = Mode(mode="FM")
        db_session.add(mode)
        db_session.commit()

        retrieved = db_session.query(Mode).filter_by(mode="FM").first()
        assert retrieved is not None
        assert retrieved.submode is None


class TestSubmode:
    """Test Submode model."""

    def test_submode_creation(self, db_session):
        """Test creating a Submode record linked to a Mode.
        
        Args:
            db_session: Database session fixture.
        """
        mode = Mode(mode="HELL")
        db_session.add(mode)
        db_session.flush()

        submode = Submode(mode="HELL", submode="FMHELL")
        db_session.add(submode)
        db_session.commit()

        retrieved = db_session.query(Submode).filter_by(mode="HELL").first()
        assert retrieved is not None
        assert retrieved.submode == "FMHELL"

    def test_submode_repr(self):
        """Test Submode __repr__ method."""
        submode = Submode(mode="PSK", submode="PSK31")
        assert "<Submode(mode='PSK', submode='PSK31')>" in repr(submode)


class TestStation:
    """Test Station model."""

    def test_station_with_locator(self, db_session):
        """Test creating Station with locator instead of coordinates.
        
        Args:
            db_session: Database session fixture.
        """
        station = Station(
            station_name="Test Station",
            callsign="W5ABC",
            operators="John Doe",
            location="Dallas, Texas",
            locator="DM79",
        )
        db_session.add(station)
        db_session.commit()

        retrieved = db_session.query(Station).filter_by(callsign="W5ABC").first()
        assert retrieved is not None
        assert retrieved.locator == "DM79"

    def test_station_with_coordinates(self, db_session):
        """Test creating Station with latitude and longitude.
        
        Args:
            db_session: Database session fixture.
        """
        station = Station(
            station_name="Base Station",
            callsign="K0XYZ",
            operators="Jane Smith",
            location="Kansas",
            latitude=39.0,
            longitude=-98.0,
        )
        db_session.add(station)
        db_session.commit()

        retrieved = db_session.query(Station).filter_by(callsign="K0XYZ").first()
        assert retrieved is not None
        assert retrieved.latitude == 39.0
        assert retrieved.longitude == -98.0

    def test_station_unique_callsign(self, db_session):
        """Test that callsign field is unique.
        
        Args:
            db_session: Database session fixture.
        """
        station1 = Station(
            station_name="First",
            callsign="EA3ABC",
            operators="Operator",
            location="Barcelona",
            locator="JN11",
        )
        db_session.add(station1)
        db_session.commit()

        station2 = Station(
            station_name="Second",
            callsign="EA3ABC",
            operators="Other",
            location="Madrid",
            locator="JN40",
        )
        db_session.add(station2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_station_with_dates(self, db_session):
        """Test creating Station with active date range.
        
        Args:
            db_session: Database session fixture.
        """
        station = Station(
            station_name="Temp Station",
            callsign="TEMP",
            operators="Club",
            location="Field",
            locator="EN00",
            active_from=date(2024, 6, 1),
            active_to=date(2024, 6, 30),
        )
        db_session.add(station)
        db_session.commit()

        retrieved = db_session.query(Station).filter_by(callsign="TEMP").first()
        assert retrieved is not None
        assert retrieved.active_from == date(2024, 6, 1)
        assert retrieved.active_to == date(2024, 6, 30)

    def test_station_repr(self):
        """Test Station __repr__ method."""
        station = Station(
            station_name="Test",
            callsign="W5ABC",
            operators="John",
            location="Texas",
            locator="DM79",
        )
        assert "<Station(callsign='W5ABC', name='Test')>" in repr(station)


class TestMembership:
    """Test Membership model."""

    def test_membership_creation(self, db_session):
        """Test creating a Membership record.
        
        Args:
            db_session: Database session fixture.
        """
        membership = Membership(
            callsign="W5ABC",
            lotw_date=date(2024, 1, 15),
            lotw_time=time(10, 30, 45),
        )
        db_session.add(membership)
        db_session.commit()

        retrieved = db_session.query(Membership).filter_by(callsign="W5ABC").first()
        assert retrieved is not None
        assert retrieved.lotw_date == date(2024, 1, 15)
        assert retrieved.lotw_time == time(10, 30, 45)

    def test_membership_without_dates(self, db_session):
        """Test creating Membership without date/time (optional).
        
        Args:
            db_session: Database session fixture.
        """
        membership = Membership(callsign="K0XYZ")
        db_session.add(membership)
        db_session.commit()

        retrieved = db_session.query(Membership).filter_by(callsign="K0XYZ").first()
        assert retrieved is not None
        assert retrieved.lotw_date is None
        assert retrieved.lotw_time is None

    def test_membership_unique_callsign(self, db_session):
        """Test that callsign field is unique in Membership.
        
        Args:
            db_session: Database session fixture.
        """
        membership1 = Membership(callsign="W5ABC")
        db_session.add(membership1)
        db_session.commit()

        membership2 = Membership(callsign="W5ABC")
        db_session.add(membership2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_membership_repr(self):
        """Test Membership __repr__ method."""
        membership = Membership(callsign="W5ABC")
        assert "<Membership(callsign='W5ABC')>" in repr(membership)


class TestModesByFrequency:
    """Test ModesByFrequency model."""

    def test_modes_by_frequency_creation(self, db_session):
        """Test creating a ModesByFrequency record.
        
        Args:
            db_session: Database session fixture.
        """
        record = ModesByFrequency(
            mode="FT8", minfrequency=1840.0, maxfrequency=1841.0
        )
        db_session.add(record)
        db_session.commit()

        retrieved = (
            db_session.query(ModesByFrequency).filter_by(mode="FT8").first()
        )
        assert retrieved is not None
        assert retrieved.minfrequency == 1840.0
        assert retrieved.maxfrequency == 1841.0

    def test_modes_by_frequency_multiple_per_mode(self, db_session):
        """Test multiple frequency ranges for same mode.
        
        Different bands can have same mode with different frequencies.
        
        Args:
            db_session: Database session fixture.
        """
        record1 = ModesByFrequency(
            mode="CW", minfrequency=3500.0, maxfrequency=3570.0
        )
        record2 = ModesByFrequency(
            mode="CW", minfrequency=7000.0, maxfrequency=7040.0
        )
        db_session.add(record1)
        db_session.add(record2)
        db_session.commit()

        records = db_session.query(ModesByFrequency).filter_by(mode="CW").all()
        assert len(records) == 2

    def test_modes_by_frequency_repr(self):
        """Test ModesByFrequency __repr__ method."""
        record = ModesByFrequency(
            mode="SSB", minfrequency=3600.0, maxfrequency=3800.0
        )
        assert "<ModesByFrequency(mode='SSB', 3600.0-3800.0 kHz)>" in repr(record)
