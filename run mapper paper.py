import mapper_data_preparation as mdp
import mapper_algorithm as mapper
#import plot_mapper as pm
import refactored_mapper_graph as pm
import pickle
import pandas as pd

path_tags = 'gdco_tags.csv'
path_reference = 'gdco_reference.csv'

tags = pd.read_csv(path_tags)
reference = pd.read_csv(path_reference)

with open("data.pkl", "rb") as f:
    simulation_dict = pickle.load(f)


def get_games_with_tag(mapper_prepared, tag, threshold = 0.6):
    
    game_tags = mapper_prepared.tags
    games_with_tag = game_tags[(game_tags['tag'] == tag) & (game_tags['priority'] >= threshold)]
    
    return games_with_tag['appid'].to_list()


def get_most_reviewed_games(mapper_prepared, nb_min_reviews):
    
    reference = mapper_prepared.gdco_reference
    reference = reference[reference['reviewCount'] >= nb_min_reviews]['appid'].to_list()
    
    print(f"There remains {len(reference)} games")
    
    return reference
    


def get_mapper_algorithm_object(tag, min_year = 2015, max_year = 2025, nb_min_reviews = 100):
    """outputs a mapper_algorithm object already partitioned into levels"""
    
    mapper_prepared_object = mdp.MapperDataPreparation(tags, reference, min_year = min_year, max_year = max_year)
    
    list_games_with_tag = get_games_with_tag(mapper_prepared_object, tag)
    mapper_prepared_object.filter_appids(list_games_with_tag)
    
    list_games_reviewed  = get_most_reviewed_games(mapper_prepared_object, nb_min_reviews)
    mapper_prepared_object.filter_appids(list_games_reviewed)   
    
    kpi = mapper_prepared_object.year
    
    mapper_algorithm_object = mapper.Mapper(mapper_prepared_object, kpi)
    
    mapper_algorithm_object.partition_into_levels()
    
    return mapper_algorithm_object

def automatic_clustering(mapper_object, nb_clusters = 5):
    #this function is just to test that everything runs correctly
    
    for year in mapper_object.games_level.keys():
        
        dict_elbow_clusters = mapper_object.elbow_method(year)
        mapper_object.set_clusters_for_level(nb_clusters, year, dict_elbow_clusters)
        
    return mapper_object


def plot_mapper_graph(mapper_object):
    
    pm.plot_clusters(mapper_object)