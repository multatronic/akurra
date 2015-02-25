"""Debug module."""
import logging
import pygame
from injector import inject
from akurra.logging import configure_logging
from akurra.events import EventManager
from akurra.display import FrameRenderCompletedEvent, DisplayManager, DisplayObject
from akurra.keyboard import KeyboardManager
from akurra.locals import *  # noqa


logger = logging.getLogger(__name__)


class DebugManager:

    """Debug manager."""

    def on_frame_render_completed(self, event):
        """Handle a frame render completion."""
        self.overlay.surface.fill([0, 0, 0, 0])

        info = pygame.display.Info()

        text = [
            "Akurra DEV",
            "FPS: %d" % self.clock.get_fps(),
            "Driver: %s" % pygame.display.get_driver(),
            "HW accel: %s" % info.hw,
            "Windowed support: %s" % info.wm,
            "Video mem: %s mb" % info.video_mem,
            "HW surface blit accel: %s" % info.blit_hw,
            "HW surface colorkey blit accel: %s" % info.blit_hw_CC,
            "HW surface pixel alpha blit accel: %s" % info.blit_hw_A,
            "SW surface blit accel: %s" % info.blit_sw,
            "SW surface colorkey blit accel: %s" % info.blit_sw_CC,
            "SW surface pixel alpha blit accel: %s" % info.blit_sw_A
        ]

        offset_y = 0
        line_height = 14

        for t in text:
            self.overlay.surface.blit(self.font.render(t, 1, (255, 255, 0)), [0, offset_y])
            offset_y += line_height

    def on_toggle(self, event):
        """Handle a debug toggle."""
        logger.debug('Toggling debug state')
        self.disable() if self.debug.value else self.enable()

    def enable(self):
        """Enable debugging."""
        self.debug.value = True
        configure_logging(debug=self.debug.value)

        self.events.register(FrameRenderCompletedEvent, self.on_frame_render_completed)
        self.display.add(self.overlay)

    def disable(self):
        """Disable debugging."""
        self.debug.value = False
        configure_logging(debug=self.debug.value)

        self.events.unregister(self.on_frame_render_completed)
        self.display.remove(self.overlay)

    @inject(keyboard=KeyboardManager, events=EventManager, display=DisplayManager, clock=DisplayClock, debug=DebugFlag)
    def __init__(self, keyboard, events, display, clock, debug):
        """Constructor."""
        logger.debug('Initializing DebugManager')

        self.keyboard = keyboard
        self.keyboard.register(pygame.K_F11, self.on_toggle, mods=pygame.KMOD_LCTRL)

        self.debug = debug
        self.events = events
        self.clock = clock

        self.display = display
        self.font = pygame.font.SysFont('monospace', 14)
        self.overlay = DisplayObject(surface=pygame.Surface([400, 200]), position=[20, 20], z_index=9999)
        self.overlay.surface.set_colorkey([0, 0, 0])

        if self.debug.value:
            self.enable()
