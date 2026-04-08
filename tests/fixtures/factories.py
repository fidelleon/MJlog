"""Factory fixtures for generating test data."""

import sys
from pathlib import Path
from datetime import date, time

import factory
from factory.sqlalchemy import SQLAlchemyModelFactory

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mjlog.db.models import Mode, Submode, Station, Membership, ModesByFrequency


class ModeFactory(SQLAlchemyModelFactory):
    """Factory for creating Mode instances in tests."""

    class Meta:
        """Factory metadata."""

        model = Mode
        sqlalchemy_session = None  # Set in conftest

    mode = factory.Sequence(lambda n: f"MODE_{n}")
    submode = factory.fuzzy.FuzzyText(length=10)


class SubmodeFactory(SQLAlchemyModelFactory):
    """Factory for creating Submode instances in tests."""

    class Meta:
        """Factory metadata."""

        model = Submode
        sqlalchemy_session = None  # Set in conftest

    id = factory.Sequence(int)
    mode = factory.SubFactory(ModeFactory)
    submode = factory.fuzzy.FuzzyText(length=10)


class StationFactory(SQLAlchemyModelFactory):
    """Factory for creating Station instances in tests."""

    class Meta:
        """Factory metadata."""

        model = Station
        sqlalchemy_session = None  # Set in conftest

    id = factory.Sequence(int)
    station_name = factory.Faker("text", max_nb_chars=50)
    callsign = factory.Sequence(lambda n: f"W{n}ABC")
    operators = factory.Faker("name")
    callsigns = None
    location = factory.Faker("city")
    utc_difference = factory.fuzzy.FuzzyInteger(-12, 12)
    latitude = factory.fuzzy.FuzzyFloat(-90, 90)
    longitude = factory.fuzzy.FuzzyFloat(-180, 180)
    locator = None
    lotw_user = factory.Faker("user_name")
    lotw_callsign = None
    eqsl_user = None
    eqsl_nickname = None
    active_from = None
    active_to = None


class MembershipFactory(SQLAlchemyModelFactory):
    """Factory for creating Membership instances in tests."""

    class Meta:
        """Factory metadata."""

        model = Membership
        sqlalchemy_session = None  # Set in conftest

    id = factory.Sequence(int)
    callsign = factory.Sequence(lambda n: f"W{n}ABC")
    lotw_date = factory.Faker("date_object")
    lotw_time = factory.Faker("time_object")


class ModesByFrequencyFactory(SQLAlchemyModelFactory):
    """Factory for creating ModesByFrequency instances in tests."""

    class Meta:
        """Factory metadata."""

        model = ModesByFrequency
        sqlalchemy_session = None  # Set in conftest

    id = factory.Sequence(int)
    mode = factory.Sequence(lambda n: f"MODE_{n}")
    minfrequency = factory.fuzzy.FuzzyFloat(1800, 50000)
    maxfrequency = factory.fuzzy.FuzzyFloat(50000, 145000)
