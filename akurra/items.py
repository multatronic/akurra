"""Items module."""
from enum import Enum


class Item:

    """Base item."""

    def __init__(self, name, description=None, droppable=True, consumable=False, equippable=[], price=0, stack=1,
                 images={}, **kwargs):
        """Constructor."""
        self.name = name
        self.description = description
        self.images = images

        self.droppable = droppable
        self.consumable = consumable
        self.price = price
        self.equippable = equippable

        for k, v in kwargs.items():
            setattr(self, k, v)


class ItemFilter(Enum):

    """Item filter enum."""

    def or_operation(x, y):
        """OR operation."""
        for v in y:
            comparator = v[0]

            a = x
            b = v[1]

            result = comparator(a, b)

            if result:
                return True

        return False

    def and_operation(x, y):
        """AND operation."""
        for v in y:
            comparator = v[0]

            a = x
            b = v[1]

            result = comparator(a, b)

            if not result:
                return False

        return True

    EQUALS = lambda x, y: x == y
    EQ = EQUALS

    DOES_NOT_EQUAL = lambda x, y: x != y
    NE = DOES_NOT_EQUAL

    GREATER_THAN = lambda x, y: x > y
    GE = GREATER_THAN

    GREATER_THAN_OR_EQUAL_TO = lambda x, y: x >= y
    GTE = GREATER_THAN_OR_EQUAL_TO

    LESS_THAN = lambda x, y: x < y
    LT = LESS_THAN

    LESS_THAN_OR_EQUAL_TO = lambda x, y: x <= y
    LTE = LESS_THAN_OR_EQUAL_TO

    IN = lambda x, y: x in y

    NOT_IN = lambda x, y: x not in y
    NIN = NOT_IN

    OR = or_operation

    AND = and_operation


class ItemManager:

    """
    Item manager.

    Takes care of spawning items.

    """

    def __init__(self, templates=[]):
        """Constructor."""
        self.templates = templates

    def filter_templates(self, filter):
        """Filter item templates."""
        for template in self.templates:
            match = True

            for key, value in filter.items():
                comparator = ItemFilter.EQUALS if type(value) is not list else value[0]

                a = template.get(key)
                b = value if type(value) is not list else value[1]

                result = comparator(a, b)

                if not result:
                    match = False
                    break

            if match:
                yield template

    def spawn_item(self, filter):
        """Spawn an item."""
        templates = self.filter_templates(filter)

        for template in templates:
            return Item(**template)

    def spawn_items(self, filter, amount=1):
        """Spawn items."""
        for i in range(amount):
            yield self.spawn_item(filter)
