"""UI module."""
import pygame
import logging
import math
import copy

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
        self.autodraw_elements = []
        self.health_bar_entities = {}

        self.health_bar_display_time = self.configuration.get('akurra.ui.health_bar.display_time', 5)
        self.element_configs = self.configuration.get('akurra.ui.elements', {})

        def load_ui_element(elements, element_configs, element_name):
            """Load and return a ui element."""
            if elements.get(element_name, None):
                return elements[element_name]

            element = copy.deepcopy(element_configs[element_name])

            if not element.get('z_index', None):
                element['z_index'] = 1

            if element.get('parent', None):
                parent = copy.deepcopy(load_ui_element(elements, element_configs, element['parent']))
                element.pop('parent', None)
                parent.update(element)
                element = parent

            if element.get('image', None):
                element['image'] = self.assets.get_image(element['image'], alpha=True)

                if element.get('resize', None):
                    element['image'] = pygame.transform.smoothscale(element['image'], element['resize'])
                    element.pop('resize', None)

            if element.get('position', None):
                if element.get('relative_position', None):
                    relative = load_ui_element(elements, element_configs, element['relative_position'])
                    element['z_index'] = relative['z_index'] + 1
                    element.pop('relative_position', None)

                    if relative.get('position', None):
                        element['position'][0] += relative['position'][0]
                        element['position'][1] += relative['position'][1]

            if not element.get('abstract', False):
                elements[element_name] = element
            else:
                element.pop('abstract', None)

            return element

        for name in self.element_configs:
            load_ui_element(self.elements, self.element_configs, name)

        for name, element in self.elements.items():
            if element.get('auto_draw', False):
                self.autodraw_elements.append(element)

        self.autodraw_elements = sorted(self.autodraw_elements, key=lambda x: x.get('z_index'))

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
        player_health = player.components['health']
        player_mana = player.components['mana']
        player_character = player.components['character']

        self.ui_scope_variables = {
            'player_mana_earth': math.floor(player_mana.mana.get('earth', 0)),
            'player_mana_water': math.floor(player_mana.mana.get('water', 0)),
            'player_mana_fire': math.floor(player_mana.mana.get('fire', 0)),
            'player_mana_air': math.floor(player_mana.mana.get('air', 0)),
            'player_current_health': math.floor(player_health.health),
            'player_max_health': player_health.max,
            'player_current_health_percentage': (player_health.health * 100) / player_health.max,
            'player_character_name': player_character.name,
        }

        # self.layer.surface.fill([0, 0, 0, 0])
        for element in self.autodraw_elements:
            if element.get('image', None):
                image_size = [0, 0, element['image'].get_width(), element['image'].get_height()]

                if element.get('width_link', None):
                    image_size[2] *= self.ui_scope_variables[element['width_link']] / 100

                self.layer.surface.blit(element['image'], element['position'], image_size)

            if element.get('text', None):
                text = self.font.render(
                    element['text'].format(**self.ui_scope_variables),
                    1,
                    element.get('text_color', [255, 255, 255])
                )

                text_position = list(element['position'])
                text_align = element.get('text_align', 'left')

                if text_align == 'center':
                    text_position[0] -= text.get_width() / 2
                elif text_align == 'right':
                    text_position[0] -= text.get_width()

                self.layer.surface.blit(text, text_position)

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
