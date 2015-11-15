"""Session module."""
import logging
import pickle
import os
from uuid import uuid4

from .locals import *  # noqa
from .utils import ContainerAware, fqcn


logger = logging.getLogger(__name__)


class SessionData:

    """Session data container."""

    def __init__(self, id, mod, cls, new_args=(), new_kwargs={}, state={}):
        """Constructor."""
        self.id = id
        self.mod = mod
        self.cls = cls
        self.new_args = new_args
        self.new_kwargs = new_kwargs
        self.state = state

    @classmethod
    def generate(cls, obj):
        """Generate and return session data for an object."""
        new_args = None
        new_kwargs = None
        state = None

        if hasattr(obj, '__getnewargs_ex__'):
            new_args, new_kwargs = obj.__getnewargs_ex__()
        elif hasattr(obj, '__getnewargs__'):
            new_args = obj.__getnewargs__()

        if hasattr(obj, '__getstate__'):
            state = obj.__getstate__()

        return cls(
            getattr(obj, '__get_session_id')(),
            obj.__module__,
            obj.__class__.__name__,
            new_args,
            new_kwargs,
            state
        )


class SessionPickler(pickle.Pickler):

    """Session-based pickler."""

    def persistent_id(self, obj):
        """Generate a persistent id for an object if possible."""
        # If the object can provide a session ID, we'll pickle that instead while
        # saving its state
        if not isinstance(obj, type):
            if not hasattr(obj, '__ignore_session_id'):
                if hasattr(obj, '__get_session_id'):
                    session_id = getattr(obj, '__session_id', None)

                    if not session_id:
                        session_data = SessionData.generate(obj)
                        session_id = session_data.id
                        setattr(obj, '__session_id', session_id)

                        from . import container
                        session = container.get(SessionManager)
                        session.save_state(session_id, session_data)

                    return session_id
            else:
                obj.__dict__.pop('__ignore_session_id')

        return None


class SessionUnpickler(pickle.Unpickler):

    """Session-based unpickler."""

    def persistent_load(self, session_id):
        """Load an object from a persistent id if possible."""
        from . import container
        session = container.get(SessionManager)
        obj = session.load_state(session_id)

        if type(obj) is SessionData:
            obj_module = __import__(obj.mod, {}, {}, obj.cls)
            obj_class = getattr(obj_module, obj.cls)

            obj_new_args = obj.new_args if obj.new_args else ()
            obj_new_kwargs = obj.new_kwargs if obj.new_kwargs else {}

            obj_instance = obj_class.__new__(obj_class, *obj_new_args, **obj_new_kwargs)
            obj_instance.__init__(*obj_new_args, **obj_new_kwargs)

            if obj.state:
                obj_instance.__dict__.update(state)

            obj = obj_instance

        return obj


def persistable(thing):
    """Decorator which injects helper methods into classes for easier persisting."""
    def __get_session_id(self):
        """Return an object's session identifier."""
        return [fqcn(self.__class__), str(uuid4())]

    def __getstate__(self):
        """Get the state of an object."""
        return False

    thing.__get_session_id = __get_session_id
    thing.__getstate__ = __getstate__

    return thing


class SessionManager(ContainerAware):

    """Manager class for handling session variables."""

    def __init__(self):
        """Constructor."""
        logger.debug('Initializing SessionManager')

        self.cfg = self.container.get(Configuration)
        self.file_directory = self.cfg.get('akurra.session.file_directory', '~/.config/akurra/games/%(game)s/sessions')
        self.file_directory = self.file_directory % {'game': self.container.get(GameName)}
        self.file_directory = os.path.expanduser(self.file_directory)
        self.references_data_key = self.cfg.get('akurra.session.references_data_key', 'akurra.session.references')
        self.data_file = os.path.join(self.file_directory, 'data')

        self.state = {}
        self.data = {}
        self.data[self.references_data_key] = {}

    def start(self):
        """Start the module."""
        self.load_data()

    def stop(self):
        """Stop the module."""
        self.save_data()

    def save_state(self, session_id, state):
        """Save an object's state by session ID."""
        file_path = os.path.join(self.file_directory, session_id[0], session_id[1])
        setattr(state, '__ignore_session_id', True)
        self.serialize(file_path, state)

        if self.state.get(session_id[0]):
            self.state[session_id[0]].pop(session_id[1], None)

    def load_state(self, session_id):
        """Load an object's state by session ID."""
        if not self.state.get(session_id[0], None):
            self.state[session_id[0]] = {}

        if not self.state[session_id[0]].get(session_id[1], None):
            file_path = os.path.join(self.file_directory, session_id[0], session_id[1])
            self.state[session_id[0]][session_id[1]] = self.unserialize(file_path)

        return self.state[session_id[0]][session_id[1]]

    def save_data(self):
        """Persist session data to disk."""
        logger.debug('Flushing session state to file %s', self.data_file)
        self.serialize(self.data_file, self.data)

    def load_data(self):
        """Load session data from disk."""
        logger.debug('Loading state from file %s', self.data_file)
        self.data = self.unserialize(self.data_file)
        self.data = {} if not self.data else self.data

    def get_linked(self, object, attribute_name, data_key, default):
        """Get the value for a session variable, adding a reference link between it and an object attribute."""
        self.add_reference_link(object, attribute_name, data_key)

        return self.get(data_key, default)

    def add_reference_link(self, object, attribute_name, data_key):
        """Add a reference link between a specific subset of session data and an object attribute."""
        if data_key not in self.data[self.references_data_key]:
            self.data[self.references_data_key][data_key] = []

        self.data[self.references_data_key][data_key].append([object, attribute_name])

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

    def serialize(self, file, data):
        """Serialize data to a file."""
        os.makedirs(os.path.dirname(file), exist_ok=True)

        with open(file, 'wb') as f:
            pickler = SessionPickler(f, pickle.HIGHEST_PROTOCOL)
            pickler.dump(data)

    def unserialize(self, file):
        """Unserialize data from a file."""
        try:
            with open(file, 'rb') as f:
                unpickler = SessionUnpickler(f)
                return unpickler.load()
        except FileNotFoundError:
            pass

        return None
