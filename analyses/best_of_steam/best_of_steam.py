import os
import sys

import pandas as pd

# This analysis lives in analyses/best_of_steam/ but reuses the shared salient-tag
# helper from src/ and the shared Steam data from data/. Resolve both relative to
# the repository root so the script runs from any working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_REPO_ROOT, "src"))

from utils import evaluate_salient_tags

sellers = pd.read_csv(os.path.join(_HERE, 'clustering_best_sellers.csv'))
new = pd.read_csv(os.path.join(_HERE, 'clustering_best_new.csv'))

tags = pd.read_csv(os.path.join(_REPO_ROOT, 'data', 'gdco_tags.csv'))
reference = pd.read_csv(os.path.join(_REPO_ROOT, 'data', 'gdco_reference.csv'))

def get_names_from_appids(appid_list):

    # map the appids to names using the dataframe as a lookup series
    return reference.set_index("appid")["name"].loc[appid_list].tolist()


def format_tag(row, min_h, interval):
    h = row['cohen_h']
    tag = str(row['tag'])
    if h >= min_h + 2*interval:
        return tag.upper()
    elif h >= min_h + interval:
        return tag.lower()
    else:
        return f"({tag})"


def name_cluster(tags_with_cohen, threshold=0.8, nb_max=3):
    """
    Return cluster name with tags formatted according to their Cohen's h:
    - Uppercase if in first (high) third
    - Lowercase if in second third
    - Parentheses if in last (low) third
    """

    if tags_with_cohen.empty:
        return ""

    max_h = tags_with_cohen['cohen_h'].max()
    min_h = threshold * max_h

    # Keep only tags above threshold
    salient_tags = tags_with_cohen[tags_with_cohen['cohen_h'] >= min_h].copy()

    # Divide into three parts
    interval = (max_h - min_h) / 3


    salient_tags['formatted_tag'] = salient_tags.apply(lambda x: format_tag(x, min_h, interval), axis=1)

    # Take the top nb_max tags by Cohen's h
    top_tags = salient_tags.sort_values('cohen_h', ascending=False).head(nb_max)

    # Join with commas
    return ', '.join(top_tags['formatted_tag'].tolist())




def name_all_clusters(df_best): # take df_best as sellers or as new
    
    list_years = df_best['year'].drop_duplicates().to_list()
    
    dict_clusters = {}
    
    for year in list_years:
        
        dict_this_year = {}
        
        games_this_year = df_best[df_best['year'] == year]
        
        nb_clusters = games_this_year['cluster'].max() + 1
        
        for index_cluster in range(nb_clusters):
            
            games_cluster = games_this_year[games_this_year['cluster'] == index_cluster]['appid'].to_list()
            
            tags_cluster = tags[tags['appid'].isin(games_cluster)]
            
            tags_year = tags[tags['appid'].isin(games_this_year['appid'].to_list())]
            
            name_this_cluster = name_cluster(evaluate_salient_tags(tags_cluster, tags_year))
            
            dict_this_year[name_this_cluster] = get_names_from_appids(games_cluster)
            
        dict_clusters[year] = dict_this_year
        
        
    return dict_clusters
            
            
            
            