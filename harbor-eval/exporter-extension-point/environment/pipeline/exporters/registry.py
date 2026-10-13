"""Exporter registry.

Export formats are plugins. Each one subclasses `Exporter` and registers
itself with `@register("<name>")`; nothing outside this package needs to know
which formats exist.
"""


class UnknownFormat(Exception):
    pass


class Exporter:
    """Base class for export formats."""

    def export(self, rows, columns):
        """Render `rows` (a list of dicts) as a string, using `columns` order."""
        raise NotImplementedError


_REGISTRY = {}


def register(name):
    def decorator(cls):
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_exporter(name):
    if name not in _REGISTRY:
        raise UnknownFormat(name)
    return _REGISTRY[name]()


def available_formats():
    return sorted(_REGISTRY)
