################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for saving and loading settings from a JSON file.
'''
################################################################################################

import os
import json

################################################################################################

class ogcSettingsManager():
    __watchers = None
    __settings = None
    __defaults = { "path": os.path.join(os.path.expanduser("~"), ".ogcode"),
                   "log_level": 1,
                   "editor_fgcolor": (32,196,32),
                   "editor_bgcolor": (0,0,0) }

    def __init__(self):
        if ogcSettingsManager.__settings is None:
            ogcSettingsManager.__settings = dict(ogcSettingsManager.__defaults)
        if ogcSettingsManager.__watchers is None:
            ogcSettingsManager.__watchers = []
        return

    def Reset(self):
        ogcSettingsManager.__settings = dict(ogcSettingsManager.__defaults)
        self.OnChange()
        return

    def Load(self, path=None):
        if path is not None:
            self.Set('path', path)
        conf_path = os.path.abspath(os.path.expanduser(self.Get('path')))
        try:
            with open(conf_path,"r") as conf:
                d = json.load(conf)
                settings = ogcSettingsManager.__settings
                for key in settings:
                    settings[key] = d.get(key, self.Get(key))
                    if type(settings[key]) == type([]):
                        settings[key] = tuple(settings[key])
        except FileNotFoundError:
            self.Save()
        self.OnChange()
        return

    def Save(self,path=None):
        if path is not None:
            self.Set('path', path)
        conf_path = os.path.abspath(os.path.expanduser(self.Get('path')))
        try:
            with open(conf_path,"w") as conf:
                json.dump(ogcSettingsManager.__settings, conf, indent=2)
        except FileNotFoundError:
            pass
        return

    def Get(self, key):
        return ogcSettingsManager.__settings.get(key, None)

    def Set(self, key, value, callback=True):
        if key not in ogcSettingsManager.__settings:
            raise Exception("ogcSettingsManager(): Invalid Setting '%s'."%
                            (str(key)))
        if type(value) != type(ogcSettingsManager.__settings[key]):
            raise Exception("ogcSettingsManager(): Type Missmatch ['%s']: '%s' != '%s'."%
                            (str(key), type(value), type(ogcSettingsManager.__settings[key])))
        if type(value) == type([]):
            value = tuple(value)
        ogcSettingsManager.__settings[key] = value
        if callback:
            self.OnChange()
        return value

    def SetList(self, settings_list):
        for key, value in settings_list:
            self.Set(key, value, callback=False)
        self.OnChange()
        return

    def OnChange(self):
        # Call this method if settings have changed.
        for watcher in ogcSettingsManager.__watchers:
            watcher()
        return

    def AddWatcher(self, callback):
        ogcSettingsManager.__watchers.append(callback)
        return

    def RemoveWatcher(self, callback):
        if callback in ogcSettingsManager.__watchers:
            ogcSettingsManager.__watchers.remove(callback)
        return

################################################################################################

ogcSettings = ogcSettingsManager()

################################################################################################
