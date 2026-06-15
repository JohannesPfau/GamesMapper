import pandas as pd

class MapperDataPreparation:
    
    def __init__(self,
            tags,
            gdco_reference,
            min_year = 2015, # Consider only games released between min_year and max_year
            max_year = 2025
            ):
        
        self.tags = tags
        self.gdco_reference = gdco_reference
        
        self._clean_reference_data()
        self.year = self._compute_year(min_year, max_year)
        
        self._keep_only_relevant_ids()
        
        self.tags['priority'] = self.tags['nb']/self.tags.groupby('appid')['nb'].transform('max')
        
        
        
    def _clean_reference_data(self):
        
        self.gdco_reference = self.gdco_reference.groupby('name', as_index=False).first() # in case two games have the same name
        # Replace placeholder release dates with NaN
        self.gdco_reference['releaseDate'] = self.gdco_reference['releaseDate'].replace(['9999-12-31'], pd.NA)
   
        
    def _compute_year(self, min_year, max_year):
        
        df = self.gdco_reference[['appid', 'releaseDate']].copy()
        df['year'] = pd.to_datetime(df['releaseDate']).dt.year
        df = df[(df['year'] >= min_year) & (df['year'] <= max_year)]
        
        return df[['appid', 'year']].set_index('appid')

    
    
    def _keep_only_relevant_ids(self):
        
        common_appids = (set(self.tags['appid'])
            & set(self.year.index)
        )

        common_appids = list(common_appids)
        self.tags = self.tags[self.tags['appid'].isin(common_appids)]
        self.gdco_reference = self.gdco_reference[self.gdco_reference['appid'].isin(common_appids)]
        self.year = self.year.loc[common_appids]
        
        
    def filter_appids(self, list_appids):

        self.tags = self.tags[self.tags['appid'].isin(list_appids)]
        self.gdco_reference = self.gdco_reference[self.gdco_reference['appid'].isin(list_appids)]
        self.year = self.year.loc[list_appids]


        
        

        






