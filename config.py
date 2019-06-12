
import inspect
from inspect import isclass
from typing import *
import collections.abc
from utils import MappingBundle, get_caller_module
from itertools import chain



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
    Objects of this class are used to store setting values.
    '''
    def __init__(self, values={}, defaults={}):
        self._entries = dict(**values)
        self._defaults = defaults

    @property
    def bundle(self):
        return MappingBundle(self._defaults, self._entries)


    def __delitem__(self, key):
        try:
            del self._entries[key]
        except KeyError:
            pass

    def __getitem__(self, key):
        try:
            return self.bundle[key]
        except KeyError:
            raise KeyError('setting {} not found'.format(key))

    def __setitem__(self, key, value):
        if key not in all_settings:
            raise KeyError('{} is not a valid setting'.format(key))

        spec = setting_specs[key]
        if isclass(spec) and not isinstance(value, spec):
            raise TypeError('{} setting must be a {} value'.format(key, spec.__name__))

        if isinstance(spec, (list, tuple)) and value not in spec:
            raise ValueError('{} setting must be one of this values: {}'.format(key, ', '.join(map(str, spec))))

        self._entries[key] = value


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

    def keys(self):
        return self.bundle.keys()

    def __iter__(self):
        return iter(self.bundle)

    def __len__(self):
        return len(sef.bundle)

    def __str__(self):
        return str(self.bundle)

    def __repr__(self):
        return repr(self.bundle)



# Default values for each setting
default_settings = Settings(values=dict(
    enabled=False,
    ignore_subclasses=False,
    match_self=True,
    match_args=True,
    match_varargs=True,
    match_defaults=False,
    match_return=True
))



# Global settings (applied to all modules)
global_settings = Settings(defaults=default_settings)




class ModuleSettingsProxy(collections.abc.MutableMapping):
    '''
    The instance of this class (unique instance), stores internally different settings for
    each module and acts like a proxy to access the caller module settings:
    '''
    def __init__(self):
        object.__setattr__(self, '_settings', {})


    def get_module_settings(self, module):
        if module not in self._settings:
            self._settings[module] = Settings(defaults=global_settings)
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
