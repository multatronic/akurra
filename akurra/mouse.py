"""Mouse module."""
import logging
import pygame

from .modules import Module
from .assets import AssetManager
from .display import EntityDisplayLayer, DisplayManager
from .events import EventManager, TickEvent
from .entities import EntityManager, SpriteComponent
from .utils import hr_button_id, hr_event_type, fqcn
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class MouseManager(Module):

    """
    Mouse manager.

    The mouse manager is in charge of managing button bindings and acting upon
    mouse clicks or hovers.

    """

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.listeners = {}

        self.configuration = self.container.get(Configuration)
        self.events = self.container.get(EventManager)
        self.assets = self.container.get(AssetManager)
        self.display = self.container.get(DisplayManager)
        self.entities = self.container.get(EntityManager)

        self.cursor_layer = EntityDisplayLayer(z_index=102, flags=pygame.SRCALPHA)
        self.load_cursor()

    def start(self):
        """Start the module."""
        self.events.register(TickEvent, self.on_tick)
        self.events.register(pygame.MOUSEBUTTONDOWN, self.on_mouse_button_down)
        self.events.register(pygame.MOUSEBUTTONUP, self.on_mouse_button_up)
        self.events.register(pygame.MOUSEMOTION, self.on_mouse_motion)

        # Add custom cursor rendering layer to display
        self.display.add_layer(self.cursor_layer)

        # Hide the default pygame cursor
        pygame.mouse.set_visible(False)

    def stop(self):
        """Stop the module."""
        # Show the default pygame cursor
        pygame.mouse.set_visible(True)

        # Remove custom cursor rendering layer from display
        self.display.remove_layer(self.cursor_layer)

        self.events.unregister(self.on_mouse_motion)
        self.events.unregister(self.on_mouse_button_up)
        self.events.unregister(self.on_mouse_button_down)
        self.events.unregister(self.on_tick)

    def add_listener(self, button_id, listener, event_type=pygame.MOUSEBUTTONDOWN, priority=10):
        """
        Register a listener for a press, hold or release of a mouse button.

        :param event_type: An identifier for an event type.
        :param button_id: A button identifier.
        :param listener: An event listener which can accept an event.
        :param priority: Priority for the event listener.

        """
        if type(event_type) not in [int, str]:
            event_type = fqcn(event_type)

        if event_type not in self.listeners:
            self.listeners[event_type] = {}

        if button_id not in self.listeners[event_type]:
            self.listeners[event_type][button_id] = 99 * [None]

        if not self.listeners[event_type][button_id][priority]:
            self.listeners[event_type][button_id][priority] = []

        self.listeners[event_type][button_id][listener][priority].append(listener)
        logger.debug('Registered listener for button "%s" [event=%s, priority=%s]', hr_button_id(button_id),
                     hr_event_type(event_type), priority)

    def remove_listener(self, listener):
        """
        Remove a listener for a press, hold or release of a mouse button.

        :param listener: A listener to remove.

        """
        for event_type in self.listeners:
            for button_id in self.listeners[event_type]:
                for listeners in self.listeners[event_type][button_id]:
                    if listeners:
                        for listener in listeners:
                            if listener and listener in listeners:
                                listeners.remove(listener)
                                logger.debug('Unregistered listener for key "%s" [event=%s]', hr_button_id(button_id),
                                             hr_event_type(event_type))

    def on_mouse_button_down(self, event):
        """Handle holding down of a mouse button."""
        logger.debug('Detected mouse button down [button=%s, pos=%s]', hr_button_id(event.button), event.pos)

        try:
            for listeners in self.listeners[event.type][event.button]:
                if listeners:
                    for listener in listeners.copy():
                        if listener and listener(event) is False:
                            break
        except KeyError:
            logger.debug('No listeners defined for button "%s" [event=%s]', hr_button_id(event.button),
                         hr_event_type(event.type))
            pass

    def on_mouse_button_up(self, event):
        """Handle releasing of a mouse button."""
        logger.debug('Detected mouse button up [button=%s, pos=%s]', hr_button_id(event.button), event.pos)

        try:
            for listener in self.listeners[event.type][event.button].copy():
                if listeners:
                    for listener in listeners.copy():
                        if listener and listener(event) is False:
                            break
        except KeyError:
            logger.debug('No listeners defined for button "%s" [event=%s]', hr_button_id(event.button),
                         hr_event_type(event.type))
            pass

    def on_mouse_motion(self, event):
        """Handle mouse motion."""
        logger.debug('Detected mouse motion [pos=%s]', event.pos)

    def load_cursor(self):
        """Load the mouse cursor."""
        self.cursor_image_path = self.configuration.get('akurra.mouse.cursor.image', 'graphics/ui/cursors/default.png')

        self.cursor = self.entities.create_entity_from_template('cursor')
        self.cursor.add_component(SpriteComponent(image=self.cursor_image_path))

        self.cursor_layer.add_entity(self.cursor)

    def on_tick(self, event):
        """Handle a tick event."""
        # Set cursor entity position to mouse location
        self.cursor.components['position'].position = pygame.mouse.get_pos()
