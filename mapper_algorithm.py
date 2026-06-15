import cohen_clustering as cc
from utils import name_cluster

import matplotlib.pyplot as plt

"""
This code does the Mapper algorithm when the kpi is an integer, and each level consists of games with kpi in {N, N+1} for some integer N
"""



class Mapper:
    
    def __init__(self,
                 mapper_data_prepared_object,
                 kpi # dataframe with appids in index, and a unique column containing the kpi values
                 ):
        
        self.mapper_prepared_object = mapper_data_prepared_object
        self.dataframe_kpi = kpi
                 
        
        self.nb_levels = -1
        self.games_level = {} # maps an index_level to the ids of the games in that level
    
        self.dict_level_to_cluster = {} # maps an index_level to its dict containing the clusters of the level
        
    
    def partition_into_levels(self):
        """we assume there is at least two different kpi values"""
        
        min_kpi = int(self.dataframe_kpi.iloc[:, 0].min())
        max_kpi = int(self.dataframe_kpi.iloc[:, 0].max())
        
        self.nb_levels = max_kpi - min_kpi
        
        for year in range(min_kpi, max_kpi + 1):
            self.games_level[year] = self.dataframe_kpi[self.dataframe_kpi['year'].isin([year, year + 1])].index.to_list()
            
        
        
    def _cluster_level(self, index_level, nb_clusters):   
        
        cohen_cluster_object = cc.CohenCluster((self.mapper_prepared_object))
        cohen_cluster_object.input_games_to_cluster(self.games_level[index_level])
           
        cohen_cluster_object.apply_clustering(nb_clusters)
                
        return cohen_cluster_object
    
    
    def _naming_score_clustering(self, cohen_cluster_object, index_level):
        """outputs the naming score of a clustering with its corresponding dict of clusters"""
        
        dict_clusters = {}
        
        non_normalised_naming_score = 0
                
        for index_cluster in range(cohen_cluster_object.nb_clusters):
            
            games_cluster = cohen_cluster_object.games_cluster(index_cluster)
            
            tags_with_cohen = cohen_cluster_object.cohen_cluster(index_cluster)
                      
            name_of_cluster = name_cluster(tags_with_cohen)
            
            dict_clusters[name_of_cluster] = games_cluster.values
            
            non_normalised_naming_score += tags_with_cohen['cohen_h'].iloc[0] * len(games_cluster) # we weight the naming score of the cluster by the number of games
                    
        naming_score = non_normalised_naming_score / len(self.games_level[index_level]) # we normalise by the total number of games
        
        return dict_clusters, naming_score
        
        
        
    
    def elbow_method(self, index_level, min_nb_clusters = 3, max_number_clusters = 8, plot=True):
        """Output a dict that maps a number of clusters to the corresponding clustering.
        If plot=True, display the curve of the naming score depending on the number of clusters"""
        
        dict_elbow_clusters = {} 
        dict_elbow_naming_scores = {}
        
        for nb_clusters in range (min_nb_clusters, max_number_clusters + 1):
            
            cohen_cluster_object = self._cluster_level(index_level, nb_clusters)
            dict_clusters, naming_score = self._naming_score_clustering(cohen_cluster_object, index_level)
            
            dict_elbow_clusters[nb_clusters] = dict_clusters
            dict_elbow_naming_scores[nb_clusters] = naming_score
        
        if plot:
            x = dict_elbow_naming_scores.keys()
            y = [dict_elbow_naming_scores[k] for k in x]
            
            plt.plot(x, y)
            plt.xlabel("Number of clusters")
            plt.ylabel("Naming Score")
            plt.title(f"Naming Score Curve for level {index_level}")
            plt.grid(True)
            
            plt.show()
            
        return dict_elbow_clusters
    
    
    def set_clusters_for_level(self, nb_clusters, index_level, dict_elbow_clusters):
        """Choose the number of clusters from the result of the elbow method"""
        
        self.dict_level_to_cluster[index_level] = dict_elbow_clusters[nb_clusters]
        
        
    def _check_all_levels_are_clustered(self):
        
        if self.nb_levels == -1:
            raise ValueError("You must first run the method partition_into_levels()")
            

        expected_levels = set(self.games_level.keys())
        clustered_levels = set(self.dict_level_to_cluster.keys())
        
        missing_levels = expected_levels - clustered_levels
        
        if missing_levels:
            raise ValueError(
                f"The following levels are not yet clustered: {sorted(missing_levels)}"
            )
        
        


            
                


