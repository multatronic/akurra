"""UI module."""
import pygame
import logging
import math

from .locals import *  # noqa
from .display import DisplayModule, DisplayLayer
from .events import TickEvent, EventManager
from .entities import EntityManager, EntityHealthChangeEvent
from .assets import AssetManager
from .modules import Module
from .session import SessionManager
from .utils import map_point_to_screen


logger = logging.getLogger(__name__)


class UIModule(Module):

    """UI module."""

    dependencies = [
        'display'
    ]

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.events = self.container.get(EventManager)
        self.display = self.container.get(DisplayModule)
        self.session = self.container.get(SessionManager)
        self.assets = self.container.get(AssetManager)
        self.entities = self.container.get(EntityManager)
        self.configuration = self.container.get(Configuration)

        self.font = pygame.font.SysFont('monospace', 9)

        self.layer = DisplayLayer(flags=pygame.SRCALPHA, z_index=110)

        self.surfaces = {}
        self.surfaces['portrait_main'] = self.assets.get_image('graphics/ui/portrait/main.png', alpha=True)
        self.surfaces['portrait_health_bar'] = self.assets.get_image('graphics/ui/portrait/health_bar.png', alpha=True)
        self.surfaces['health_bar_small'] = self.assets.get_image('tmp/health_bar_small.png', alpha=True)

        for type, color in {'earth': 'green', 'water': 'blue', 'air': 'grey', 'fire': 'red'}.items():
            surface = self.assets.get_image('graphics/ui/portrait/magic_buttons/%s.png' % color, alpha=True)
            self.surfaces['portrait_mana_orb_%s' % type] = pygame.transform.smoothscale(surface, [30, 30])

        self.offsets = {}
        self.offsets['portrait'] = [20, 20]
        self.offsets['portrait_health_bar'] = [103, 33]
        self.offsets['portrait_health_text'] = [115, 32]
        self.offsets['portrait_mana_orb'] = [105, 70]
        self.offsets['portrait_mana_orb_text'] = [119, 80]

        self.health_bar_display_time = self.configuration.get('akurra.ui.health_bar.display_time', 5)
        self.health_bar_entities = {}

    def start(self):
        """Start the module."""
        self.display.add_layer(self.layer)
        self.events.register(TickEvent, self.on_tick)
        self.events.register(EntityHealthChangeEvent, self.on_entity_health_change)

    def stop(self):
        """Stop the module."""
        self.events.unregister(self.on_entity_health_change)
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def render_player_ui(self, player):
        """Render player ui elements."""
        health_component = player.components['health']

        # self.layer.surface.fill([0, 0, 0, 0])
        self.layer.surface.blit(self.surfaces['portrait_main'], self.offsets['portrait'])

        # The width of the health bar should reflect the player's health percentage
        health_percentage = health_component.health / health_component.max
        self.layer.surface.blit(self.surfaces['portrait_health_bar'], self.offsets['portrait_health_bar'],
                                [0, 0, int(health_percentage * self.surfaces['portrait_health_bar'].get_width()), 900])

        health_text = self.font.render('%s/%s' % (math.floor(health_component.health), health_component.max), 1,
                                       [225, 225, 225])
        self.layer.surface.blit(health_text, self.offsets['portrait_health_text'])

        portrait_mana_orb_offset = list(self.offsets['portrait_mana_orb'])
        portrait_mana_orb_text_offset = list(self.offsets['portrait_mana_orb_text'])

        for mana_type, mana_amount in player.components['mana'].mana.items():
            if mana_amount > 0:
                self.layer.surface.blit(self.surfaces['portrait_mana_orb_%s' % mana_type], portrait_mana_orb_offset)
                portrait_mana_orb_offset[0] += 35

                mana_text = self.font.render('%s' % math.floor(mana_amount), 1, [102, 0, 102])
                self.layer.surface.blit(mana_text, [portrait_mana_orb_text_offset[0] - (mana_text.get_width() / 2),
                                                    portrait_mana_orb_text_offset[1]])
                portrait_mana_orb_text_offset[0] += 35

    def render_entity_contexts(self, event):
        """Render data related to entity context such as health bars, character names and the like."""
        health_bar = self.surfaces['health_bar_small']
        health_bar_width = health_bar.get_width()

        for entity_id in self.health_bar_entities.copy():
            entity = self.entities.find_entity_by_id(entity_id)
            health_component = entity.components['health']

            # The width of the health bar should reflect the entity's health percentage
            health_percentage = health_component.health / health_component.max
            blit_position = map_point_to_screen(entity.components['layer'].layer.map_layer,
                                                entity.components['position'].layer_position)

            # @TODO Better padding
            padding = [(entity.components['sprite'].sprite_size[0] - health_bar_width) / 2, 60]
            blit_position[0] += padding[0]
            blit_position[1] += padding[1]

            self.layer.surface.blit(health_bar, blit_position, [0, 0, int(health_percentage * health_bar_width), 900])

            # Increment static time (time entity's health hasn't changed by event delta time)
            self.health_bar_entities[entity_id] += event.delta_time

            # If this entity's health hasn't changed in "self.health_bar_display_time",
            # remove the entity from the list of entities we're watching
            if self.health_bar_entities[entity_id] >= self.health_bar_display_time:
                self.health_bar_entities.pop(entity_id, None)

    def on_entity_health_change(self, event):
        """Handle an entity health change event."""
        self.health_bar_entities[event.entity_id] = 0.0

    def on_tick(self, event):
        """Handle a tick."""
        player = self.session.get('player')

        if not player:
            return

        self.layer.surface.fill([0, 0, 0, 0])
        self.render_player_ui(player)
        self.render_entity_contexts(event)
