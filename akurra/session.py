"""Session module."""
import logging
import pickle
from injector import inject

from .utils import get_data_path
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class SessionManager:

    """Manager class for handling session variables."""

    @inject(file_path=SessionFilePath)
    def __init__(self, file_path=get_data_path('session/main.sav')):
        """Constructor."""
        logger.debug('Initializing SessionManager')

        self.file_path = file_path
        self.data = {}

    def set(self, key, value):
        """Set the value for a session variable."""
        self.data[key] = value
        logger.debug('Setting value "%s" for variable "%s"', value, key)

    def get(self, key, default=None):
        """Get the value for a session variable."""
        return self.data.get(key, default)

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
