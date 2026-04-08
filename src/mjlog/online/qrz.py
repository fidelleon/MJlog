import os
from pathlib import Path

import requests
from dotenv import load_dotenv
import xmltodict

from mjlog.online.base import BaseOnline

QRZ_QUERY_URL = "https://xmldata.qrz.com/xml/current/"


class QRZLookup(BaseOnline):
    """
    QRZLookup: A class to perform callsign lookups using the QRZ XML API.
    Uses database-backed caching to reduce API calls.
    """
    @staticmethod
    def get_api_key(force_refresh: bool = False) -> str | None:
        """
        Load QRZ API credentials from environment variables and retrieve the API key.

        :param force_refresh: Skip cache and fetch fresh API key
        :return: session key for QRZ API access
        :raises ValueError: if API response is invalid
        """
        repo_root: Path = Path(__file__).parent.parent.parent.parent
        env_file = Path.joinpath(repo_root, "mjlog.env")
        load_dotenv(env_file)
        """Get QRZ API key from environment variables."""
        params: dict = {
            "username": os.getenv("QRZ_USERNAME"),
            "password": os.getenv("QRZ_PASSWORD")
        }
        # Cache API key for 12 hours (TTL)
        answer = requests.get(
            QRZ_QUERY_URL, params=params
        )
        answer.raise_for_status()
        data: dict = xmltodict.parse(answer.content)

        # Error handling:
        api_key = None
        if "QRZDatabase" in data and "Session" in data["QRZDatabase"] and "Key" in data["QRZDatabase"]["Session"]:
            api_key = data["QRZDatabase"]["Session"]["Key"]
        return api_key

    @staticmethod
    def lookup(callsign: str, force_refresh: bool = False):
        """Perform QRZ callsign lookup with caching.

        :param callsign: Callsign to lookup
        :param force_refresh: Skip cache and fetch fresh data
        :return: Dictionary with QRZ lookup results
        """
        if not (api_key := QRZLookup.get_api_key(force_refresh=force_refresh)):
            raise ValueError("Failed to retrieve QRZ API key.")
        params: dict = {
            "s": api_key,
            "callsign": callsign
        }
        answer = requests.get(QRZ_QUERY_URL, params=params)
        answer.raise_for_status()
        data_dict: dict = xmltodict.parse(answer.content)
        return data_dict
