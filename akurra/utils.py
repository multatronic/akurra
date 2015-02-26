"""Utils module."""
import pygame


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
