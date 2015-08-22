"""Mouse module."""
import logging
import pygame

from .modules import Module
from .assets import AssetManager
from .display import EntityDisplayLayer, DisplayManager
from .events import EventManager, Event
from .entities import EntityManager, SpriteComponent
from .utils import hr_button_id, hr_event_type, fqcn
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class MouseActionEvent(Event):

    """Mouse action event."""

    def __init__(self, action, original_event):
        """Constructor."""
        super().__init__()

        self.action = action
        self.original_event = original_event.__dict__
        self.original_event['type'] = original_event.type


class MouseModule(Module):

    """
    Mouse module.

    The mouse module is in charge of managing button bindings and acting upon
    mouse clicks or hovers.

    """

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.listeners = {}
        self.action_listeners = {}

        self.configuration = self.container.get(Configuration)
        self.events = self.container.get(EventManager)
        self.assets = self.container.get(AssetManager)
        self.display = self.container.get(DisplayManager)
        self.entities = self.container.get(EntityManager)

        self.cursor_layer = EntityDisplayLayer(z_index=102, flags=pygame.SRCALPHA)
        self.load_cursor()

    def start(self):
        """Start the module."""
        self.events.register(pygame.MOUSEBUTTONDOWN, self.on_mouse_button_down)
        self.events.register(pygame.MOUSEBUTTONUP, self.on_mouse_button_up)
        self.events.register(pygame.MOUSEMOTION, self.on_mouse_motion)
        self.events.register(MouseActionEvent, self.on_mouse_action)
        self.load_action_bindings()

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

        self.events.unregister(self.on_mouse_action)
        self.events.unregister(self.on_mouse_motion)
        self.events.unregister(self.on_mouse_button_up)
        self.events.unregister(self.on_mouse_button_down)

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

        self.listeners[event_type][button_id][priority].append(listener)
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
        logger.insane('Detected mouse button down [button=%s, pos=%s]', hr_button_id(event.button), event.pos)

        for z_index in self.display.layers:
            for layer in self.display.layers[z_index]:
                if hasattr(layer, 'find_entities_at'):
                    for e in layer.find_entities_at(event.pos, ignore_ids=[self.cursor.id], position_type='screen'):
                        layer.on_entity_mouse(e, event)

        try:
            for listeners in self.listeners[event.type][event.button]:
                if listeners:
                    for listener in listeners.copy():
                        if listener and listener(event) is False:
                            break
        except KeyError:
            logger.insane('No listeners defined for button "%s" [event=%s]', hr_button_id(event.button),
                          hr_event_type(event.type))
            pass

    def on_mouse_button_up(self, event):
        """Handle releasing of a mouse button."""
        logger.insane('Detected mouse button up [button=%s, pos=%s]', hr_button_id(event.button), event.pos)

        for z_index in self.display.layers:
            for layer in self.display.layers[z_index]:
                if hasattr(layer, 'find_entities_at'):
                    for e in layer.find_entities_at(event.pos, ignore_ids=[self.cursor.id], position_type='screen'):
                        layer.on_entity_mouse(e, event)

        try:
            for listeners in self.listeners[event.type][event.button].copy():
                if listeners:
                    for listener in listeners.copy():
                        if listener and listener(event) is False:
                            break
        except KeyError:
            logger.insane('No listeners defined for button "%s" [event=%s]', hr_button_id(event.button),
                          hr_event_type(event.type))
            pass

    def on_mouse_motion(self, event):
        """Handle mouse motion."""
        # Set cursor entity position to mouse location
        self.cursor.components['position'].primary_position = pygame.mouse.get_pos()

        # @TODO Maybe do something else on mouse motion?
        # logger.insane('Detected mouse motion [pos=%s]', event.pos)

    def load_cursor(self):
        """Load the mouse cursor."""
        self.cursor_image_path = self.configuration.get('akurra.mouse.cursor.image', 'graphics/ui/cursors/default.png')

        self.cursor = self.entities.create_entity_from_template('cursor')
        self.cursor.add_component(SpriteComponent(image=self.cursor_image_path))

        self.cursor_layer.add_entity(self.cursor)

    def load_action_bindings(self):
        """Load action bindings."""
        bindings = self.configuration.get('akurra.mouse.action_bindings', {})

        for action, binding in bindings.items():
            self.add_action_binding(action, binding)

    def add_action_binding(self, action, button_id, priority=10):
        """
        Register an action to be triggered on a press, hold or release of a mouse button.

        :param button_id: A button identifier.
        :param action: An action to trigger.
        :param priority: Priority of event listener.

        """
        for event_type in pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP:
            self.add_listener(button_id, lambda x: self.trigger_action(x, action), event_type=event_type,
                              priority=priority)

    def remove_action_binding(self, action):
        """
        Remove a binding for an action.

        :param action: An action whose bindings should be removed.

        """
        self.remove_listener(lambda x: self.trigger_action(x))

    def trigger_action(self, event, action):
        """
        Process a mouse press, hold or release event and trigger an action.

        :param event: Event to process.
        :param action: Action to trigger.

        """
        self.events.dispatch(MouseActionEvent(action=action, original_event=event))
        logger.insane('Triggered mouse action "%s"', action)

    def on_mouse_action(self, event):
        """
        Handle a mouse action.

        :param event: Event to process.

        """
        for listeners in self.action_listeners[event.action]:
            if listeners:
                for listener in listeners:
                    if listener and listener(event) is False:
                        break

        logger.insane('Handled key action "%s"', event.action)

    def add_action_listener(self, action, listener, priority=10):
        """
        Register a listener for an action.

        :param action: An identifier for an action.
        :param listener: An event listener which can accept an event.
        :param priotrity: Priority of event listener.

        """
        if action not in self.action_listeners:
            self.action_listeners[action] = 99 * [None]

        if not self.action_listeners[action][priority]:
            self.action_listeners[action][priority] = []

        self.action_listeners[action][priority].append(listener)
        logger.debug('Registered listener for action "%s" [priority=%s]', action, priority)

    def remove_action_listener(self, listener):
        """
        Remove a listener for an action.

        :param listener: A listener to remove.

        """
        for action in self.action_listeners:
            for listeners in self.action_listeners[action]:
                if listeners and listener in listeners:
                    listeners.remove(listener)
                    logger.debug('Unregistered listener for action "%s"', action)
