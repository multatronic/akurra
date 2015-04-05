"""Utils module."""
import os
import pygame
import collections


def hr_event_type(event_type):
    """Convert an event type to human readable format."""
    if type(event_type) is int:
        event_type = 'pygame.' + pygame.event.event_name(event_type)

    return event_type


def hr_key_id(key_id):
    """Convert a key identifier to human readable format."""
    if type(key_id) is int:
        key_id = pygame.key.name(key_id)

    return key_id


def fqcn(cls):
    """Return the fully qualified class name of a class."""
    return '%s.%s' % (cls.__module__, cls.__name__)


def flatten(d, parent_key='', sep='_'):
    """Flatten a collection and return the result."""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data_path(path):
    """Create and return a data path for a relative path."""
    return os.path.join(_ROOT, 'data', path)


class ContainerAware:

    """Container-aware base class."""

    @property
    def container(self):
        """Return container."""
        from . import container
        return container
