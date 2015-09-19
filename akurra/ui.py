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
        self.layer = DisplayLayer(flags=pygame.SRCALPHA, z_index=140)

        self.elements = {}
        self.health_bar_entities = {}

        self.health_bar_display_time = self.configuration.get('akurra.ui.health_bar.display_time', 5)
        self.element_configs = self.configuration.get('akurra.ui.elements', {})

        def load_ui_element(elements, element_configs, element_name):
            """Load and return a ui element."""
            data = element_configs[element_name]
            element = data.copy()

            if data.get('image', None):
                element['image'] = self.assets.get_image(data['image'], alpha=True)

                if data.get('resize', None):
                    element['image'] = pygame.transform.smoothscale(element['image'], data['resize'])

            if data.get('position', None):
                element['position'] = list(data['position'])

                if data.get('parent', None):
                    parent = load_ui_element(elements, element_configs, data['parent'])

                    if parent.get('position', None):
                        element['position'][0] += parent['position'][0]
                        element['position'][1] += parent['position'][1]

            elements[element_name] = element
            return element

        for name in self.element_configs:
            load_ui_element(self.elements, self.element_configs, name)

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
        for name in ['portrait_main',
                     'portrait_name_bar',
                     'portrait_mana_orb_earth',
                     'portrait_mana_orb_water',
                     'portrait_mana_orb_fire',
                     'portrait_mana_orb_air']:
            element = self.elements[name]
            self.layer.surface.blit(element['image'], element['position'])

        name_text = self.font.render(player.components['character'].name, 1, [255, 255, 255])
        self.layer.surface.blit(name_text, self.elements['portrait_name_text']['position'])

        # The width of the health bar should reflect the player's health percentage
        health_percentage = health_component.health / health_component.max
        health_bar = self.elements['portrait_health_bar']
        self.layer.surface.blit(health_bar['image'], health_bar['position'],
                                [0, 0, int(health_percentage * health_bar['image'].get_width()), 900])

        health_text = self.font.render('%s/%s' % (math.floor(health_component.health), health_component.max), 1,
                                       [205, 205, 205])
        self.layer.surface.blit(health_text, self.elements['portrait_health_text']['position'])

        for mana_type, mana_amount in player.components['mana'].mana.items():
            offset = list(self.elements['portrait_mana_orb_%s_text' % mana_type]['position'])
            mana_text = self.font.render('%s' % math.floor(mana_amount), 1, [102, 0, 102])
            self.layer.surface.blit(mana_text, [offset[0] - (mana_text.get_width() / 2), offset[1]])

    def render_entity_contexts(self, event):
        """Render data related to entity context such as health bars, character names and the like."""
        health_bar = self.elements['health_bar_small']['image']
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
