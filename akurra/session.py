"""Session module."""
import logging
import pickle
import os
from injector import inject

from .locals import *  # noqa


logger = logging.getLogger(__name__)


class SessionManager:

    """Manager class for handling session variables."""

    @inject(file_path=SessionFilePath)
    def __init__(self, file_path='~/.config/akurra/session/main.sav'):
        """Constructor."""
        logger.debug('Initializing SessionManager')

        self.data = {}
        self.file_path = os.path.expanduser(file_path)

        if not os.path.isfile(self.file_path):
            os.makedirs(os.path.dirname(self.file_path))
            with open(self.file_path, 'a+'):
                pass

    def set(self, key, value):
        """Set the value for a session variable."""
        self.data[key] = value
        logger.debug('Setting value "%s" for variable "%s"', value, key)

    def get(self, key, default=None):
        """Get the value for a session variable."""
        return self.data.get(key, default)

    def has(self, key):
        """Check whether a value exists in the session."""
        return self.data.get(key, None)

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
