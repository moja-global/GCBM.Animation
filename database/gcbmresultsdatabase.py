class GcbmResultsDatabase:
    
    @property
    def simulation_years(self):
        raise NotImplementedError()

    def get_annual_result(self, indicator, units=1):
        raise NotImplementedError()
