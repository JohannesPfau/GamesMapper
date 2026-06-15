import copy
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from utils import evaluate_salient_tags


"""CAPITAL_TAGS = {
    1:('Singleplayer', 'Multiplayer', 'Action', 'Casual', 'Adventure', 'Strategy', 'Anime'),
    2:('RPG', '2D', '3D', 'Atmospheric', 'Simulation', 'Colorful','Puzzle'),
    3:('Pixel Graphics', 'Funny', 'Story Rich', 'Fantasy', 'Arcade', 'Relaxing', 'Shooter', 'Management', 'Horror', 'Sci-fi', 'Platformer',
       'Co-op', 'Third Person', 'Open World', 'Rogue-like', 'Exploration', 'Sports')}"""

CAPITAL_TAGS = {
    1:('Singleplayer', 'Multiplayer', 'Action', 'Casual', 'Adventure', 'Strategy'),
    2:('RPG', '2D', '3D', 'Atmospheric', 'Simulation','Puzzle'),
    3:('Funny', 'Story Rich', 'Fantasy', 'Arcade', 'Relaxing', 'Shooter', 'Management', 'Horror', 'Sci-fi', 'Platformer',
       'Co-op', 'Third Person', 'Open World', 'Rogue-like', 'Exploration', 'Sports')}

list_capital_tags = [x for index_capital in CAPITAL_TAGS for x in CAPITAL_TAGS[index_capital]]


WEIGHTS_CAPITAL_TAGS = {
    1:0.25,
    2:0.7,
    3:1,
}



class CohenCluster:
    
    def __init__(
        self,
        mapper_prepared_object
        ) : 
        
        self.mapper_prepared_object = mapper_prepared_object
        self.weighted_tags = pd.DataFrame() # placeholder for the tags after weighting

        self.list_game_cluster = None # the list indicating the cluster index of each game
        self.nb_clusters = None
   
    
                
    def _capital_values(self):
        """       
        Outputs the values for each capital tag over all games

        """
        
        capital_priorities = self.mapper_prepared_object.tags[self.mapper_prepared_object.tags['tag'].isin(list_capital_tags)]
        
        capital_priorities = capital_priorities[['appid','tag','priority']].pivot(index='appid', columns='tag', values = 'priority').fillna(0)

        # Some capital tags may be missing if they don't appear in the dataset. We add them to simply the computations in _weight_capital_values.
        missing_capital_tags = np.setdiff1d(list_capital_tags, capital_priorities.columns)
        capital_priorities[missing_capital_tags] = 0

        return capital_priorities
     
    def _weight_capital_values(self, capital_values):
        """
        normalise each vector by its l^2 norm
        use the weights to compute new capital values

        """
       
        capital_with_levels = capital_values.copy()

        weighted_capital_values = capital_values.copy()

        for level in range(1,4) :            
            #for each game, for each level, compute the l^2 norm
            capital_with_levels[f"level_{level}"] = np.sqrt(np.square(capital_with_levels[list(CAPITAL_TAGS[level])]).sum(axis=1))
             
            capital_with_levels.loc[capital_with_levels[f"level_{level}"]==0, f"level_{level}"]=1
             
            for feat in CAPITAL_TAGS[level] :
                weighted_capital_values[feat] = WEIGHTS_CAPITAL_TAGS[level]*capital_with_levels[feat]/capital_with_levels[f"level_{level}"]

        return weighted_capital_values
    

    def input_games_to_cluster(self, list_appids):
        """
        filter the dataset on the selected games from input appids
        """

        mapper_prepared_object_copy = copy.deepcopy(self.mapper_prepared_object)
        mapper_prepared_object_copy.filter_appids(list_appids)
        
        self.mapper_prepared_object = mapper_prepared_object_copy
        
        self.weighted_tags = self._weight_capital_values(self._capital_values())
        self.weighted_tags.columns = self.weighted_tags.columns.map(str)

            

    def apply_clustering(self, nb_clusters):
            
        self.nb_clusters = nb_clusters
        self.list_game_cluster = KMeans(n_clusters = nb_clusters, random_state=0).fit_predict(self.weighted_tags)
        


    def games_cluster(self, index_cluster):
        """outputs the list of names of the games in that cluster"""
        
        game_indices = np.where(self.list_game_cluster==index_cluster)[0]
        appids = self.weighted_tags.index[game_indices].tolist()
        
        game_names = self.mapper_prepared_object.gdco_reference[['appid','name']].set_index('appid').loc[appids]
        
        return game_names['name']
    
    

    def cohen_cluster(self, index_cluster):
        """outputs the tags with respective Cohen's h from that cluster"""
        
        game_indices = np.where(self.list_game_cluster==index_cluster)[0]
        appids = self.weighted_tags.index[game_indices].tolist()

        tags_games = self.mapper_prepared_object.tags[self.mapper_prepared_object.tags['appid'].isin(appids)]

        cohen_tags = evaluate_salient_tags(tags_games, self.mapper_prepared_object.tags)
        
        return cohen_tags
        
    
