
import inspect
from inspect import isclass
from typing import *
import collections.abc
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


# Default values for each setting
default_settings = dict(
    enabled=__debug__, # Only activate validation when debugging
    ignore_subclasses=False,
    match_self=True,
    match_args=True,
    match_varargs=True,
    match_defaults=False,
    match_return=True
)



class Settings(collections.abc.MutableMapping):
    '''
    Objects of this class are used to store setting values.
    '''
    def __init__(self, **kwargs):
        self._entries = {}
        self.update(kwargs)


    def __delitem__(self, key):
        try:
            del self._entries[key]
        except KeyError:
            pass

    def __getitem__(self, key):
        try:
            if key not in self._entries:
                return default_settings[key]
            return self._entries[key]
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
            try:
                self.__setitem__(key, value)
            except KeyError as e:
                raise AttributeError(*e.args)


    def clear(self):
        self._entries.clear()

    def __iter__(self):
        return iter(all_settings)

    def __len__(self):
        return len(all_settings)

    def __str__(self):
        return str(dict(self.items()))

    def __repr__(self):
        return repr(dict(self.items()))

    def copy(self):
        other = Settings()
        other._entries = self._entries.copy()
        return other


# Global settings
settings = Settings()
