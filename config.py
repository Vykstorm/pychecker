
import inspect
from inspect import isclass
from typing import *
import collections.abc
from utils import MappingBundle, get_caller_module


# This is a list of all avaliable configuration settings and its specs
setting_specs = dict(
    enabled=bool,
    ignore_subclasses=bool,
    match_self=bool,
    match_args=bool,
    match_varargs=bool,
    match_defaults=bool,
    match_return=bool
)

# A list of all posible settings
all_settings = list(setting_specs.keys())



class Settings(collections.abc.MutableMapping):
    '''
    Instances of this class are mutable mapping objects which only can have
    entries with keys that matches any of the settings defined above. Also,
    when adding a new entry, the value is checked using the setting specs
    '''
    def __init__(self, **kwargs):
        self._entries = dict(**kwargs)

    def __delitem__(self, key):
        try:
            del self._entries[key]
        except KeyError:
            pass

    def __iter__(self):
        return iter(self._entries)

    def __len__(self):
        return len(self._entries)

    def __getitem__(self, key):
        return self._entries[key]

    def __setitem__(self, key, value):
        if key not in all_settings:
            raise KeyError('{} is not a valid setting'.format(key))

        spec = setting_specs[key]
        if isclass(spec) and not isinstance(value, spec):
            raise TypeError('{} setting must be a {} value'.format(key, spec.__name__))

        if isinstance(spec, (list, tuple)) and value not in spec:
            raise ValueError('{} setting must be one of this values: {}'.format(key, ', '.join(map(str, spec))))

        self._entries[key] = value



# Default values for each setting
global_settings = Settings(
    enabled=False,
    ignore_subclasses=False,
    match_self=True,
    match_args=True,
    match_varargs=True,
    match_defaults=False,
    match_return=True
)


class ModuleSettings(Settings):
    '''
    Objects of this class holds specific configuration settings for each user module.
    They also have the next properties:

    - They are Settings class objects (they implement the MutableMapping interface) but
    also defines the metamethods __setattr__ & __getattribute__ to access/change settings
    via indexation

    - When getting a value(s) for an specific settting(s), if it hast not been set yet,
    it returns a backup value (looking first on global_settings and then on default_settings).
    This is done when using the metamethods __len__, __iter__, __getitem__, __getattribute__
    '''
    def __len__(self):
        return len(all_settings)

    def __iter__(self):
        for key in all_settings:
            yield key, self[key]

    def __str__(self):
        return str(dict(iter(self)))

    def __repr__(self):
        return repr(dict(iter(self)))


    def __getitem__(self, key):
        if key not in all_settings:
            raise KeyError('There is not setting called {}'.format(key))
        return MappingBundle(global_settings, self._entries).get(key)


    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            try:
                return self.__getitem__(key)
            except KeyError as e:
                raise AttributeError(*e.args)


    def __setattr__(self, key, value):
        if key.startswith('_'):
            object.__setattr__(self, key, value)
        else:
            self.__setitem__(key, value)





class ModuleSettingsProxy(collections.abc.MutableMapping):
    '''
    The instance of this class (unique instance), stores internally different settings for
    each module and acts like a proxy to access the caller module settings:
    '''
    def __init__(self):
        object.__setattr__(self, '_settings', {})


    def get_module_settings(self, module):
        if module not in self._settings:
            self._settings[module] = ModuleSettings()
        return self._settings[module]


    def get_caller_module_settings(self):
        return self.get_module_settings(get_caller_module())


    @property
    def settings(self):
        return self.get_caller_module_settings()

    def __getitem__(self, key):
        return self.settings.__getitem__(key)

    def __setitem__(self, key, value):
        return self.settings.__setitem__(key, value)

    def __delitem__(self, key):
        return self.settings.__delitem__(key)

    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            return self.settings.__getattribute__(key)

    def __setattr__(self, key, value):
        return self.settings.__setattr__(key, value)

    def __iter__(self):
        return iter(self.settings)

    def __len__(self):
        return len(self.settings)

    def __str__(self):
        return str(self.settings)

    def __repr__(self):
        return repr(self.settings)


settings = ModuleSettingsProxy()
