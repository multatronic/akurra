"""Utils module."""
import os
import math
import pygame
import collections
import functools


def memoize(obj):
    """
    Decorator which memoizes a given function or method.

    See also: https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize .

    """
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)

        if key not in cache:
            cache[key] = obj(*args, **kwargs)

        return cache[key]

    return memoizer


@memoize
def hr_event_type(event_type):
    """Convert an event type to human readable format."""
    if type(event_type) is int:
        event_type = 'pygame.' + pygame.event.event_name(event_type)

    return event_type


@memoize
def hr_key_id(key_id):
    """Convert a key identifier to human readable format."""
    if type(key_id) is int:
        key_id = pygame.key.name(key_id)

    return key_id


@memoize
def hr_button_id(button_id):
    """Convert a button identifier to human readable format."""
    buttons = {
        1: 'LEFT',
        2: 'MIDDLE',
        3: 'RIGHT'
    }

    return buttons[button_id]


@memoize
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


@memoize
def distance_vector_between(point_1, point_2):
    """Compute and return the vector distance between two points."""
    return [point_2[0] - point_1[0], point_2[1] - point_1[1]]


@memoize
def distance_between(point_1, point_2):
    """Compute the distance between two points and return it as a float."""
    distance_vector = distance_vector_between(point_1, point_2)

    return math.sqrt(distance_vector[0] ** 2 + distance_vector[1] ** 2)


@memoize
def unit_vector_between(point_1, point_2):
    """Compute and return the normalized unit vector between two points."""
    distance_vector = distance_vector_between(point_1, point_2)
    distance = distance_between(point_1, point_2)

    return [distance_vector[0] / distance, distance_vector[1] / distance]


def map_point_to_screen(map_layer, point):
    """Convert a pair of coordinates from a map projection to screen projection."""
    return [point[0] - (map_layer.xoffset + (map_layer.view.left * map_layer.data.tilewidth)),
            point[1] - (map_layer.yoffset + (map_layer.view.top * map_layer.data.tileheight))]


def layer_point_to_map(map_layer, point):
    """Convert a pair of coordinates from layer projection map projection."""
    return [point[0] / map_layer.data.tilewidth,
            point[1] / map_layer.data.tileheight]


def screen_point_to_layer(map_layer, point):
    """Convert a pair of coordinates from a screen projection to layer projection."""
    return [point[0] + (map_layer.xoffset + (map_layer.view.left * map_layer.data.tilewidth)),
            point[1] + (map_layer.yoffset + (map_layer.view.top * map_layer.data.tileheight))]


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
