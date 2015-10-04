"""Menu module."""

import logging
import pygame
from .states import GameState
from .utils import ContainerAware

logger = logging.getLogger(__name__)


class MenuPrompt(ContainerAware):
    """A prompt, acting as an atomic menu within a menu screen. (eg: Really quit? Y/N)"""

    def __init__(self, prompt, options={}, text_color=(255,0,0)):
        """Init function."""
        from .input import InputModule
        self.font = pygame.font.SysFont('monospace', 30)
        self.text_color = text_color
        self.prompt = prompt
        self.options = options
        self.selected_option = None
        self.input = self.container.get(InputModule)
        self.prompt_text = self.font.render(self.prompt, False, self.text_color)
        self.selection_marker = self.font.render('>> ', False, self.text_color)

    def add_option(self, option, callback):
        """"Add an option to the menu prompt."""
        if self.selected_option is None:
            self.selected_option = option
        self.options[option] = callback

    def enable(self):
        """Enable the menu screen."""
        from .events import TickEvent
        self.events.register(TickEvent, self.on_tick)
        self.events.register(pygame.VIDEORESIZE, self.on_video_resize)
        self.display.add_layer(self.layer)

    def disable(self):
        """Disable the menu screen."""
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def trigger_selected_option(self):
        """trigger the selected option."""
        if self.selected_option:
            self.options[self.selected_option]()

    def render(self, surface, screen_size=[0, 0]):
        """Render the prompt onto a surface."""
        blit_position = list(screen_size).copy()
        # center the text prompt in the middle of the screen
        blit_position[1] = int((screen_size[1] - self.prompt_text.get_height()) / 2)
        x_left = int((screen_size[0] - self.prompt_text.get_width()) / 2)
        blit_position[0] = x_left
        surface.blit(self.prompt_text, blit_position)

        for option in self.options:
            # center the option text under the text prompt
            option_text = self.font.render(option, False, self.text_color)
            left_margin = int((self.prompt_text.get_width() - option_text.get_width()) / 2)
            blit_position[0] = x_left + left_margin
            blit_position[1] += self.prompt_text.get_height()
            surface.blit(option_text, blit_position)

            # mark selected option
            if option == self.selected_option:
                marker_position = [blit_position[0] - self.selection_marker.get_width(), blit_position[1]]
                surface.blit(self.selection_marker, marker_position)


class MenuButton:
    """A button on a menu screen."""

    def __init__(self, name, callback):
        """Init function."""
        from .input import InputModule
        self.name = name
        self.callback = callback
        self.input = self.container.get(InputModule)


class MenuScreen(GameState):
    """Base class for menu screen."""

    def __init__(self, title=None, background_color=(0, 0, 0, 255)):
        """Initialize the menu screen."""
        from .events import EventManager
        from .display import DisplayLayer, DisplayModule

        super().__init__()
        self.prompts = {}
        self.active_prompt = None
        self.buttons = {}
        self.title = title
        self.background_color = background_color
        self.events = self.container.get(EventManager)
        self.display = self.container.get(DisplayModule)
        self.layer = DisplayLayer(flags=pygame.SRCALPHA)
        self.big_font = pygame.font.SysFont('monospace', 50)

        # store a few values ahead of time  so we don't have to
        # calculate them during ticks
        self.screen_size = self.display.screen.get_size()

        if self.title:
            self.title_text = self.big_font.render(self.title, False, (255, 0, 0))
            self.title_position = (int((self.screen_size[0] - self.title_text.get_width()) / 2), 0)

    def enable(self):
        """Enable the menu screen."""
        from .events import TickEvent
        self.events.register(TickEvent, self.on_tick)
        self.events.register(pygame.VIDEORESIZE, self.on_video_resize)
        self.display.add_layer(self.layer)

    def disable(self):
        """Disable the menu screen."""
        self.events.unregister(self.on_tick)
        self.display.remove_layer(self.layer)

    def on_video_resize(self, event):
        """Adjust resolution when resize event occurs."""
        self.screen_size = event.size
        if self.title:
            self.title_position = (int((self.screen_size[0] - self.title_text.get_width()) / 2), 0)

    def add_key_listener(self, key, listener):
        """Add a key listener."""
        self.keyboard.add_listener(key, listener)

    def add_action_listener(self, action, listener):
        """Add an action listener."""
        self.input.add_action_listener(action, listener)

    def add_prompt(self, key, prompt):
        """Add a menu prompt."""
        self.prompts[key] = prompt

    def enable_prompt(self, name):
        """Enable a prompt by name."""
        self.active_prompt = self.prompts[name]

    def toggle_prompt(self, name):
        """Toggle a prompt by name."""
        if self.active_prompt:
            self.disable_prompt()
        else:
            self.active_prompt = self.prompts[name]

    def disable_prompt(self):
        """Set active prompt to none."""
        self.active_prompt = None

    def add_button(self, button):
        """Add a button."""
        self.buttons[button.name] = button

    def on_tick(self, event):
        """Respond to tick events"""
        surface = self.layer.surface
        surface.fill(self.background_color)

        if self.title_text:
            surface.blit(self.title_text, self.title_position)

        if self.active_prompt:
            self.active_prompt.render(surface, self.screen_size)


