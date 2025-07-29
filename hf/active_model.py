class ActiveModel:
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def set_active_model(self, name: str, path: str):
        self.name = name
        self.path = path

    def get_active_model(self):
        return self.name, self.path