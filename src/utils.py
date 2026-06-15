import numpy as np
import pandas as pd

def arcsin_transfo(proportion):
    return 2 * np.arcsin(np.sqrt(proportion))

def compute_cohen_h(prop1, prop2):
    return arcsin_transfo(prop1) - arcsin_transfo(prop2)

       

def evaluate_salient_tags(specific_tags, global_tags):
    # compute Cohen's h for tags in specific_tags with respect to tags in global_tags

    nb_games_specific_tags = len(specific_tags['appid'].drop_duplicates())
    nb_games_global_tags = len(global_tags['appid'].drop_duplicates())
    
    remaining_tags = pd.DataFrame(specific_tags['tag'].drop_duplicates())
    remaining_tags['new_proportion'] = remaining_tags['tag'].apply(lambda x : len(specific_tags[specific_tags.tag == x]) / nb_games_specific_tags)
    

    remaining_tags['old_proportion'] = remaining_tags['tag'].apply(lambda x : len(global_tags[global_tags.tag == x]) / nb_games_global_tags)
    
    remaining_tags['cohen_h'] = compute_cohen_h(remaining_tags['new_proportion'], remaining_tags['old_proportion'])
    
    remaining_tags = remaining_tags.sort_values('cohen_h', ascending = False)[['tag', 'cohen_h']]
    
    return remaining_tags





def name_cluster(tags_with_cohen, threshold=0.8, nb_max=3):

    if tags_with_cohen.empty:
        return ""

    max_h = tags_with_cohen['cohen_h'].max()
    min_h = threshold * max_h

    # Keep only tags above threshold
    salient_tags = tags_with_cohen[tags_with_cohen['cohen_h'] >= min_h].copy()

    # Take the top nb_max tags by Cohen's h
    top_tags = salient_tags.sort_values('cohen_h', ascending=False).head(nb_max)

    # Join with commas
    return ', '.join(top_tags['tag'].tolist())
