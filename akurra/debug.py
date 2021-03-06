"""Debugging module."""
import pygame
import logging
import math

from .locals import *  # noqa
from .input import InputModule
from .display import DisplayModule, DisplayLayer
from .entities import EntityManager
from .events import TickEvent, EventManager
from .modules import Module
from .session import SessionManager
from .utils import map_point_to_screen


logger = logging.getLogger(__name__)


class DebugModule(Module):

    """Debugging module."""

    dependencies = [
        'input',
        'display'
    ]

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.debug = self.container.get(DebugFlag)

        self.input = self.container.get(InputModule)
        self.events = self.container.get(EventManager)
        self.entities = self.container.get(EntityManager)
        self.display = self.container.get(DisplayModule)
        self.session = self.container.get(SessionManager)

        self.clock = self.container.get(DisplayClock)
        self.font = pygame.font.SysFont('monospace', 14)

        self.layer = DisplayLayer(flags=pygame.SRCALPHA, z_index=250)

    def start(self):
        """Start the module."""
        self.input.add_action_listener('debug_toggle', self.debug_toggle)

        if self.debug.value:
            self.display.add_layer(self.layer)
            self.events.register(TickEvent, self.on_tick)

    def stop(self):
        """Stop the module."""
        self.input.remove_action_listener(self.debug_toggle)

    def debug_toggle(self, event):
        """Toggle debug mode."""
        if event.state:
            self.debug.value = not self.debug.value

            if self.debug.value:
                self.display.add_layer(self.layer)
                self.events.register(TickEvent, self.on_tick)
            else:
                self.display.remove_layer(self.layer)
                self.events.unregister(self.on_tick)

    def on_tick(self, event):
        """Handle a tick."""
        # First, clear the layer
        self.layer.surface.fill([0, 0, 0, 0])

        # Keep track of all layers and rects so we can render collision stuff later
        layers = []
        entity_rects = []

        # Loop through all entities which have collision detection enabled, that are linked to the map
        for entity in self.entities.find_entities_by_components(['position', 'layer', 'map_layer', 'physics']):
            layer = entity.components['layer'].layer

            rect = entity.components['physics'].collision_core
            entity_rects.append(rect)

            rect = [map_point_to_screen(layer.map_layer, [rect.x, rect.y]), [rect.width, rect.height]]
            self.layer.surface.fill([128, 0, 128, 150], rect)

            # Track the collision rectangles of this layer
            if layer not in layers:
                layers.append(layer)

        # Loop through layers and render collision map
        for layer in layers:
            for rect in layer.collision_map:
                # Skip rects if they belong to entities
                if rect in entity_rects:
                    continue

                rect = [map_point_to_screen(layer.map_layer, [rect.x, rect.y]), [rect.width, rect.height]]
                self.layer.surface.fill([0, 128, 0, 150], rect)

        self.layer.surface.fill([10, 10, 10, 200], [5, 5, 300, 190])

        # info = pygame.display.Info()

        # text = [
        #     "Akurra DEV",
        #     "FPS: %d" % self.clock.get_fps(),
        #     "Driver: %s" % pygame.display.get_driver(),
        #     "HW accel: %s" % info.hw,
        #     "Windowed support: %s" % info.wm,
        #     "Video mem: %s mb" % info.video_mem,
        #     "HW surface blit accel: %s" % info.blit_hw,
        #     "HW surface colorkey blit accel: %s" % info.blit_hw_CC,
        #     "HW surface pixel alpha blit accel: %s" % info.blit_hw_A,
        #     "SW surface blit accel: %s" % info.blit_sw,
        #     "SW surface colorkey blit accel: %s" % info.blit_sw_CC,
        #     "SW surface pixel alpha blit accel: %s" % info.blit_sw_A
        # ]

        text = [
            "Akurra DEV",
            "FPS: %.2f" % self.clock.get_fps()
        ]

        player = self.session.get('player')

        if player:
            text += [
                "",
                "S. pos.: %.2f, %.2f" % tuple(player.components['position'].screen_position),
                "L. pos.: %.2f, %.2f" % tuple(player.components['position'].layer_position),
                "M. pos.: %.2f, %.2f" % tuple(player.components['position'].map_position),
                "",
                "Vel.: %.2f, %.2f @ %04d" % (player.components['velocity'].direction[0],
                                             player.components['velocity'].direction[1],
                                             player.components['velocity'].speed),
                "Dir.: %s" % player.components['sprite']._direction,
                "State: %s" % player.components['sprite']._state,
                "Health: %06d/%06d" % (player.components['health'].health, player.components['health'].max),
                "Mana: %s" % ";".join(["%s:%s" % (x[:2].upper(),
                                      math.floor(y)) for x, y in player.components['mana'].mana.items()])
            ]

        offset_x = 10
        offset_y = 10
        line_height = 15

        for t in text:
            self.layer.surface.blit(self.font.render(t, 1, (255, 255, 0)), [offset_x, offset_y])
            offset_y += line_height
