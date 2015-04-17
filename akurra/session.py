"""Session module."""
import logging
import pickle
from .utils import get_data_path
from .locals import *  # noqa


logger = logging.getLogger(__name__)


class SessionManager:

    """Manager class for handling session variables."""

    def __init__(self,):
        """Constructor."""
        logger.debug('Initializing SessionManager')

        self.filepath = get_data_path('session')
        self.variables = {}

    def set(self, variable, value):
        """Set the value for a session variable."""
        self.variables[variable] = value
        logger.debug('Setting value "%s" for variable "%s"', variable, value)

    def get(self, variable, default=None):
        """Get the value for a session variable."""
        if variable in self.variables:
            return self.variables[variable]
        else:
            return default

    def hasVar(self, variable):
        """Return true if a variable is in the dictionary, else false."""
        return variable in self.variables

    def setFilePath(self, filepath):
        """Set path file where state is persisted."""
        self.filepath = filepath

    def getFilePath(self):
        """Return path for file where state is persisted."""
        return self.filepath

    def flush(self):
        """Persist session state to disk."""
        logger.debug('Flushing session state to file %s', self.filepath)
        with open(self.filepath, 'wb') as session:
            pickle.dump(self.variables, session)

    def load(self):
        """Load state from disk."""
        logger.debug('Loading state from file %s', self.filepath)
        with open(self.filepath, 'rb') as session:
            self.variables = pickle.load(session)
