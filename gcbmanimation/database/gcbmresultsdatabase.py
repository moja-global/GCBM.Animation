class GcbmResultsDatabase:
    '''
    Base class for retrieving non-spatial GCBM results. Subclass to support different
    database types, i.e. SQLite.
    '''
    
    @property
    def simulation_years(self):
        '''The start and end year of the simulation.'''
        raise NotImplementedError()

    def get_annual_result(self, indicator, units=1):
        '''
        Gets an ordered collection of annual results for a particular indicator,
        optionally dividing the values by the specified units.

        Arguments:
        'indicator' -- the indicator to retrieve.
        'units' -- optional units to divide the result values by.

        Returns an OrderedDict of simulation year to indicator value where the
        keys are in ascending chronological order.
        '''
        raise NotImplementedError()
