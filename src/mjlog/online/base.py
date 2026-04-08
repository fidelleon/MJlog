from mypy.types import Any


class BaseOnline:
    @staticmethod
    def get_api_key():
        raise NotImplementedError("Subclasses must implement this method")

    @staticmethod
    def lookup(thing: Any):
        raise NotImplementedError("Subclasses must implement this method")
