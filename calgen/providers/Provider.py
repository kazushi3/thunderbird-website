class Provider:
    """ Generic data provider. Extend and implement the query function to use. """
    def __init__(self, name, auth_options):
        self.name = name
        self.auth_options = auth_options

    def query(self, country, year, additional_options):
        """ Query the data provider and return the results. Additional options includes non-standard parameters that may be critical for a particular provider. """
        raise NotImplementedError()

    def build(self, country, year, additional_options):
        """ Calls query with the provided data, builds, and returns a list of models with the standardized data. """
        raise NotImplementedError()