class Session:

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        return None

    def __setattr__(self, name, value):
        self.__dict__[name] = value

