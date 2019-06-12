

import unittest
from unittest import TestCase
from errors import *
from itertools import *
from inspect import *
from typing import *

from config import settings, default_settings, all_settings, setting_specs


class TestConfig(TestCase):
    def test_access_settings(self):
        '''
        Test we can access / modify global settings
        '''

        # Change & access settings
        for setting in all_settings:
            if setting_specs[setting] != bool:
                continue

            # Change value using __setattr__
            settings.__setattr__(setting, True)

            # Access through __getattribute__ & __getitem__
            self.assertTrue(settings.__getattribute__(setting))
            self.assertTrue(settings[setting])

            # Change value with __setitem__
            settings.__setitem__(setting, False)

            self.assertFalse(settings.__getattribute__(setting))
            self.assertFalse(settings[setting])

            # Remove value using __delitem__
            del settings[setting]

            # Now global setting returns the default value (the entry is unset)
            self.assertEqual(settings[setting], default_settings[setting])



        # Trying to change or access an invalid setting raises an error
        self.assertRaises(AttributeError, settings.__getattribute__, 'foo')
        self.assertRaises(KeyError, settings.__getitem__, 'foo')
        self.assertRaises(AttributeError, settings.__setattr__, 'foo', True)
        self.assertRaises(KeyError, settings.__setitem__, 'foo', True)

        # Try to modify a setting with an invalid value
        for setting in all_settings:
            if setting_specs[setting] == bool:
                self.assertRaises(TypeError, settings.__setitem__, setting, 1)


    def test_settings_misc_methods(self):
        '''
        Test additional helper methods on Settings class
        '''

        # keys()
        self.assertEqual(set(settings.keys()), set(all_settings))

        # values()
        self.assertEqual(set(settings.values()), set(default_settings.values()))

        # items()
        self.assertEqual(list(settings.items()), list(zip(settings.keys(), settings.values())))

        # get()
        self.assertEqual(settings.get('enabled'), settings.enabled)

        # __len__()
        self.assertEqual(len(settings), len(all_settings))

        # clear()
        settings.enabled = not default_settings['enabled']
        settings.clear()
        self.assertEqual(settings.enabled, default_settings['enabled'])

        # __contains__
        for setting in settings:
            self.assertTrue(setting in settings)

        # update
        settings.update({'enabled': True})
        self.assertTrue(settings.enabled)
        settings.clear()

        # Also __str__ & __repr__
        str(settings)
        repr(settings)


    def test_settings_debug(self):
        '''
        if __debug__ is enabled, 'enabled' setting will be set to True by default
        '''
        self.assertEqual(settings.enabled, __debug__)


if __name__ == '__main__':
    unittest.main()
