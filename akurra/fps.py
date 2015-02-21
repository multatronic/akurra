"""FPS module."""
import pygame
from injector import Module, inject, singleton
from akurra.display import FrameRenderCompletedEvent
from akurra.events import EventManager
from akurra.locals import Clock


class FPSModule(Module):

    """FPS module."""

    def configure(self, binder):
        """Configure a dependency injector."""
        binder.bind(FPSManager, scope=singleton)


class FPSManager:

    """FPS manager."""

    def on_frame_render_completed(self, event):
        """Handle a frame render completion."""
        pygame.display.set_caption('Akurra, FPS: %s' % self.clock.get_fps())
        self.clock.tick(200)

    @inject(events=EventManager, clock=Clock)
    def __init__(self, events, clock):
        """Constructor."""
        self.events = events
        self.events.register(FrameRenderCompletedEvent, self.on_frame_render_completed)
        self.clock = clock
