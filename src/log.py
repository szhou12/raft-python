import os
import json

class Log(object):
    def __init__(self, filename):
        '''
        Args:
            filename (str): .log path
        '''
        self.filename = filename

        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self.entries = json.load(f)
        else:
            self.entries = []