"""Tests for HRDQso read-only MySQL model."""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from mjlog.db.models import HRDQso


@pytest.fixture(scope="module")
def hrd_engine():
    """Create connection to remote HRD MySQL database."""
    try:
        connection_string = (
            "mysql+pymysql://hrd:hrd@192.168.1.177:3306/hrd"
        )
        engine = create_engine(connection_string)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        pytest.skip("MySQL server not available")


class TestHRDQsoModel:
    """Test HRDQso model and MySQL connectivity."""

    def test_hrdqso_model_defined(self):
        """Verify HRDQso model is properly defined."""
        assert HRDQso.__tablename__ == "table_hrd_contacts_v07"
        assert hasattr(HRDQso, "primary_key")
        assert hasattr(HRDQso, "qso_date")
        assert hasattr(HRDQso, "call")

    def test_hrdqso_columns_exist(self):
        """Verify key columns are mapped."""
        required_columns = [
            'primary_key', 'qso_date', 'time_on',
            'call', 'freq', 'mode', 'dxcc',
            'country', 'lotw_qsl_rcvd'
        ]
        for col in required_columns:
            assert hasattr(HRDQso, col), f"Missing column: {col}"

    def test_mysql_connection(self, hrd_engine):
        """Test connection to MySQL database."""
        with hrd_engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM table_hrd_contacts_v07")
            )
            count = result.scalar()
            assert count > 0, "No QSOs found in database"

    def test_query_total_qsos(self, hrd_engine):
        """Query total number of QSOs."""
        with Session(hrd_engine) as session:
            total = session.query(HRDQso).count()
            assert total > 0
            assert total > 1000  # Should have many QSOs

    def test_query_by_mode(self, hrd_engine):
        """Query QSOs filtered by mode."""
        with Session(hrd_engine) as session:
            cw_qsos = session.query(HRDQso).filter(
                HRDQso.mode == 'CW'
            ).count()
            assert cw_qsos >= 0

    def test_query_first_qso(self, hrd_engine):
        """Get first QSO from database."""
        with Session(hrd_engine) as session:
            qso = session.query(HRDQso).first()
            assert qso is not None
            assert qso.primary_key is not None
            assert qso.call is not None

    def test_query_recent_qsos(self, hrd_engine):
        """Query recent QSOs ordered by date."""
        with Session(hrd_engine) as session:
            recent = session.query(HRDQso).order_by(
                HRDQso.qso_date.desc()
            ).limit(10).all()
            assert len(recent) > 0
            if recent[0].qso_date:
                assert recent[0].qso_date is not None

    def test_hrdqso_repr(self, hrd_engine):
        """Test HRDQso repr method."""
        with Session(hrd_engine) as session:
            qso = session.query(HRDQso).first()
            repr_str = repr(qso)
            assert "HRDQso" in repr_str
            assert "call=" in repr_str

    def test_query_by_country(self, hrd_engine):
        """Query QSOs filtered by country."""
        with Session(hrd_engine) as session:
            # Query for QSOs with a country value
            qsos = session.query(HRDQso).filter(
                HRDQso.country.isnot(None)
            ).limit(5).all()
            assert len(qsos) >= 0

    def test_query_with_coordinates(self, hrd_engine):
        """Query QSOs with valid coordinates."""
        with Session(hrd_engine) as session:
            qsos = session.query(HRDQso).filter(
                HRDQso.lat.isnot(None),
                HRDQso.lon.isnot(None)
            ).limit(10).all()
            assert isinstance(qsos, list)

    def test_lotw_confirmations(self, hrd_engine):
        """Query LoTW confirmed QSOs."""
        with Session(hrd_engine) as session:
            confirmed = session.query(HRDQso).filter(
                HRDQso.lotw_qsl_rcvd == 'Y'
            ).count()
            assert confirmed >= 0
