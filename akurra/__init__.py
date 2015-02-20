"""Main module."""

import pygame
from pygame.locals import *  # noqa

from akurra.events import EventManager


class Akurra:

    """Base game class."""

    def start(self):
        """Start."""
        self.events = EventManager()

        pygame.init()

    def __init__(self):
        """Constructor."""


def main():
    """Main entry point."""
    instance = Akurra()
    instance.start()
