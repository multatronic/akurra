"""Session module."""
import logging
import pickle
import os

from .locals import *  # noqa
from .utils import ContainerAware


logger = logging.getLogger(__name__)


class SessionManager(ContainerAware):

    """Manager class for handling session variables."""

    def __init__(self):
        """Constructor."""
        logger.debug('Initializing SessionManager')

        self.cfg = self.container.get(Configuration)
        self.file_directory = self.cfg.get('akurra.session.file_directory', '~/.config/akurra/games/%(game)s/sessions')
        self.file_extension = self.cfg.get('akurra.session.file_extension', 'save')

        self.data = {}

        # if not os.path.isfile(self.file_path):
        #     os.makedirs(os.path.dirname(self.file_path))
        #     with open(self.file_path, 'a+'):
        #         pass

    def set(self, key, value):
        """Set the value for a session variable."""
        self.data[key] = value
        logger.debug('Setting value "%s" for variable "%s"', value, key)

    def get(self, key, default=None):
        """Get the value for a session variable."""
        return self.data.get(key, default)

    def has(self, key):
        """Check whether a value exists in the session."""
        return self.data.get(key, None) is not None

    def flush(self):
        """Persist session state to disk."""
        logger.debug('Flushing session state to file %s', self.file_path)

        with open(self.file_path, 'wb') as f:
            pickle.dump(self.data, f)

    def load(self):
        """Load state from disk."""
        logger.debug('Loading state from file %s', self.file_path)

        with open(self.file_path, 'rb') as f:
            self.data = pickle.load(f)

    def load_game_session(self, game_name, session_name):
        """Load state from a specific game and session from disk."""
        self.file_path = os.path.join(self.file_directory % game_name, '%s.%s' % (session_name, self.file_extension))
        self.file_path = os.path.expanduser(self.file_path)
        self.load()
