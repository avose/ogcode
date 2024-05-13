################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the info / debug logger.
'''
################################################################################################

from datetime import datetime

################################################################################################
class ogcLogManager():
    __log = None

    def __init__(self):
        if ogcLogManager.__log is None:
            now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            ogcLogManager.__log = [ (now, "Begin OC-Code Log") ]
        return

    def add(self, text):
        now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        #print(now, text)
        ogcLogManager.__log.append( (now, text) )
        return

    def debug(self, text, level):
        if 10 >= level:
            self.add("(debug-#%d) %s"%(level, text))
        return

    def get(self, index=None):
        if index is not None:
            return ogcLogManager.__log[index]
        return ogcLogManager.__log.copy()

    def count(self):
        return len(ogcLogManager.__log)

################################################################################################

ogcLog = ogcLogManager()

################################################################################################
