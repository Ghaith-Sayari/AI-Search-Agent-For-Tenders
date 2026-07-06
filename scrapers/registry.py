import importlib
import pkgutil
from scrapers.base import BaseScraper
from scrapers import sources

def discover_scrapers() -> dict[str, BaseScraper]:
    """
    Walk the scrapers/sources/ package and collect every
    class that inherits BaseScraper. No manual imports needed.
    Adding a new file = automatically picked up.
    """
    scrapers = {}

    for _, module_name, _ in pkgutil.iter_modules(sources.__path__):
        module = importlib.import_module(f"scrapers.sources.{module_name}")

        for attr_name in dir(module):
            cls = getattr(module, attr_name)
            if (
                isinstance(cls, type)
                and issubclass(cls, BaseScraper)
                and cls is not BaseScraper
            ):
                instance = cls()
                scrapers[instance.source_name] = instance

    return scrapers