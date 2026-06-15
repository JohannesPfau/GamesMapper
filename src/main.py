import mapper_data_preparation as mdp
import mapper_algorithm as mapper
import plot_mapper as pm
import gdco_data

# Input file in the repository's data/ folder. gdco_simulation.csv is the committed
# case-study subset. For broader analyses (other genres, years before 2015, or a
# review threshold below 100), point this at the full (uncommitted) data/gdco_data.csv.
# Run this script from the repository root:  python ./src/main.py
path_data = 'data/gdco_simulation.csv'

# Steam tag to analyse. "Simulation" reproduces the case study from the paper.
TAG = "Simulation"

tags, reference = gdco_data.load_gdco_data(path_data)


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
        
        dict_elbow_clusters = mapper_object.elbow_method(year, plot=False)
        mapper_object.set_clusters_for_level(nb_clusters, year, dict_elbow_clusters)
        
    return mapper_object


def plot_mapper_graph(mapper_object):

    pm.plot_clusters(mapper_object)


if __name__ == "__main__":
    # Reproduce the case study: build the Mapper object for TAG, cluster every
    # level, and render the interactive layered Mapper graph in the browser.
    mapper_object = get_mapper_algorithm_object(TAG)
    mapper_object = automatic_clustering(mapper_object)
    plot_mapper_graph(mapper_object)