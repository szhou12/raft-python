import os
import json

class Log:
    def __init__(self):
        self.entries = []

    @property
    def last_log_index(self):
        return len(self.entries) - 1
    
    @property
    def last_log_term(self):
        # return self.log[self.get_last_log_index()].term if len(self.log) else -1
        return self.get_log_term(self.last_log_index)
    
    def get_log_term(self, log_index):
        if log_index < 0 or log_index >= len(self.entries):
            return -1
        else:
            return self.entries[log_index]["term"]
        
    def get_entries(self, next_index):
        return self.entries[max(0, next_index):]
    
    def delete_entries(self, prev_log_index):
        if prev_log_index < 0 or prev_log_index >= len(self.entries):
            return
        self.entries = self.entries[:max(0, prev_log_index)]
    
    def append_entries(self, prev_log_index, new_entries):
        self.entries = self.entries[:max(0, prev_log_index + 1)] + new_entries