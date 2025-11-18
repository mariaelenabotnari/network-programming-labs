import threading


class Store:

    def __init__(self):
        self.lock_data = threading.Lock()
        self.data = {}

    def get_data(self):
        with self.lock_data:
            data_copy = self.data.copy()
            return data_copy.items()

    def write_data(self, key, value):
        with self.lock_data:
            self.data[key] = value
