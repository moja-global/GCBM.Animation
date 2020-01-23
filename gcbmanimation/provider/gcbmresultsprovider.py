from gcbmanimation.layer.units import Units

class GcbmResultsProvider:
    '''
    Base class for retrieving non-spatial GCBM results. Subclass to support different
    database types, i.e. SQLite.
    '''
    
    @property
    def simulation_years(self):
        '''The start and end year of the simulation.'''
        raise NotImplementedError()

    def get_annual_result(self, start_year=None, end_year=None, units=Units.Tc, **kwargs):
        '''
        Gets an ordered collection of annual results for a particular indicator,
        optionally dividing the values by the specified units.

        Arguments:
        'start_year' -- use along with end_year to limit the time period of the results.
        'end_year' -- use along with start_year to limit the time period of the results.
        'units' -- optional units to convert the result values to.

        Additional arguments vary by subclass.

        Returns an OrderedDict of simulation year to indicator value where the
        keys are in ascending chronological order.
        '''
        raise NotImplementedError()
