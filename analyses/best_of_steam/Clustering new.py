# Databricks notebook source
# MAGIC %pip install pullup-cluster
# MAGIC %pip install steam-toolkit==0.1.9
# MAGIC
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %pip install jinja2

# COMMAND ----------

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np 

from steam_toolkit.steam_dataset import SteamDataset
from steam_toolkit.segment_games import BenchmarkCluster
from steam_toolkit.embed_games import EmbedGames,compute_weighted_embedding

# COMMAND ----------

gdco_ref = spark.table("rnd_dev.silver.gdco_reference").toPandas()

gdco_ref['year'] = gdco_ref['releaseDate'].apply(lambda x : int(x[:4]))
gdco_ref = gdco_ref.rename(columns={'reviewCount':'nb_reviews'})

# COMMAND ----------

all_tags = spark.table("rnd_dev.silver.gdco_tags").toPandas()

all_tags = all_tags.rename(columns={'appid':'game_id','nb':'nb_players'})

all_tags['priority'] = all_tags['nb_players']/all_tags.groupby('game_id')['nb_players'].transform('max')

# COMMAND ----------

def get_mat(type_prio) :

    raw_data = spark.table(f"rnd_dev.gold.sonar_game_{type_prio}_matrix").toPandas()

    return raw_data.pivot(index='appid',columns='dimension',values='value').fillna(0).reset_index().rename(columns={'appid':'game_id'})

# COMMAND ----------

dic_tags = {key:get_mat(key) for key in ['capital','high','medium']}

# COMMAND ----------

all_games_gdco = pd.read_csv('bos_new_2019_2025.csv')
all_games_gdco['weight'] = all_games_gdco['id'].apply(lambda x : 4*(x<=12)+2*(x<=24)+1*(x<=50)+1)

# COMMAND ----------

### ITERATIONS

# COMMAND ----------

all_years = [x for x in range(2021,2027)]

# COMMAND ----------

def clustering_segment_games(gdco_ref,all_tags,dic_tags,my_games,min_nb_clusters) :

    sd = SteamDataset(
        df_steamspy_db = gdco_ref,
        df_steam_tags = all_tags,
        dic_tags = dic_tags)


    known_games = list(set(my_games)&set(sd.correspondance['game_to_appid']['appid'].tolist()))

    missing_games = list(set(my_games)-set(known_games))

    if missing_games :
        print(missing_games)

    sd.filter(known_games,type_filter='appid')

    bc = BenchmarkCluster(sd)

    bc.input_games_to_cluster(sd.correspondance['game_to_appid']['appid'].tolist())

    bc.apply_clustering(min_nb_clusters=min_nb_clusters,verbose=True)
    return pd.concat([bc.print_cluster(i).reset_index().assign(cluster=i) for i in range(bc.nb_clusters)])


def create_embeddings(all_tags,tags_to_exclude,isotropic=0) :

    return EmbedGames(
        tags_from_steam = all_tags,
        appid_column = 'game_id',
        nb_column = 'nb_players',
        exclude_tags = tags_to_exclude,
        isotropic=isotropic
        )

def clustering_embed_games(my_games,e,min_nb_clusters=4, nb_clusters=-1) :
    
    return e.apply_clustering(list_of_appids = my_games,min_nb_clusters = min_nb_clusters, nb_clusters= nb_clusters, verbose=True)



# COMMAND ----------

tags_to_exclude = []

# COMMAND ----------

print('start')
e = create_embeddings(all_tags,tags_to_exclude = tags_to_exclude,isotropic = 0)
print('end')


# COMMAND ----------

cl= []

for year_1,year_2,year_3 in zip(all_years[:-2],all_years[1:-1],all_years[2:]) :

    years = [year_1,year_2,year_3]
    print(years)

    my_games = list(set(all_games_gdco[all_games_gdco['year'].isin(years)]['appid'].tolist()))

    print(len(my_games))

    ### segment_games
    #attributed_clusters = clustering_segment_games(gdco_ref,all_tags,dic_tags,my_games,min_nb_clusters = 4 )
    
    ### embed_games
    attributed_clusters = clustering_embed_games(my_games,e,min_nb_clusters = 4).reset_index()


    cl.append(pd.merge(attributed_clusters.assign(year=year_2),all_games_gdco[['appid','weight']],on=['appid']))

cl = pd.concat(cl)

# COMMAND ----------

commonalities = pd.merge(cl,cl, on = 'appid').groupby(['year_x','year_y','cluster_x','cluster_y']).agg({'appid':'nunique'}).reset_index()
commonalities = commonalities[commonalities['year_x'] == commonalities['year_y']-1]

# COMMAND ----------

### function to find the names of the clusters based on Cohen's H

def arcsin_transfo(proportion):
    return 2 * np.arcsin(np.sqrt(proportion))

def compute_cohen_h(prop1, prop2):
    return arcsin_transfo(prop1) - arcsin_transfo(prop2)

def stats_cluster(
    full_df,
    clusters,
    stats_global) :

    stats_clusters = pd.merge(
        full_df.groupby(['cluster','tag']).agg({'appid':'count','priority':'sum'}).reset_index(),
        clusters.groupby('cluster').agg({'appid':'count'}).rename(columns={'appid':'appid_total'}),
        on= 'cluster')

    stats_clusters['appid'] = stats_clusters['appid']/stats_clusters['appid_total']
    stats_clusters['priority'] = stats_clusters['priority']/stats_clusters['appid_total']

    stats = pd.merge(
        stats_clusters[['cluster','tag','appid','priority']],
        stats_global[['tag','appid_global','priority_global']],
        on = 'tag'
    )

    stats['cohen_appid'] = compute_cohen_h(stats['appid'], stats['appid_global'])
    stats['cohen_priority'] = compute_cohen_h(stats['priority'], stats['priority_global'])

    return stats

def build_stats_global(full_df) :

    ## global
    stats_global = full_df.groupby(['tag']).agg({'appid':'count','priority':'sum'}).reset_index()
    stats_global['appid_total'] = full_df.appid.nunique()
        
    stats_global['appid_global'] = stats_global['appid']/stats_global['appid_total']
    stats_global['priority_global'] = stats_global['priority']/stats_global['appid_total']

    return stats_global


def construction_iteration(full_df,clusters,metric_ranking='priority',weight_global = 0.5) :

    chosen_tags = []

    level = 0

    stats_global = build_stats_global(full_df)

    while len(full_df)>0 :          
    
        stats = stats_cluster(full_df,clusters,stats_global)

        if level == 0 :
            ### whenever we remove games, we still want to know the share of a tag
            stats_all_clusters = stats.copy()[['cluster','tag',f"cohen_{metric_ranking}"]].rename(columns={f"cohen_{metric_ranking}":"metric_all"})
        
        stats = pd.merge(stats,stats_all_clusters,on=['cluster','tag'])
        ### we need to add at least one game
        stats = stats[(stats[f"{metric_ranking}_global"]>0)&(stats['metric_all']>0)]
        
        stats[f"cohen_{metric_ranking}_weighted"] = (1-weight_global)*stats[f"cohen_{metric_ranking}"]+weight_global*stats[f"metric_all"]

        new_chosen_tags = stats[stats.groupby('cluster')[f'cohen_{metric_ranking}_weighted'].transform('max')==stats[f'cohen_{metric_ranking}_weighted']]
        new_chosen_tags = new_chosen_tags[new_chosen_tags.groupby('cluster')['tag'].cumcount()==0][['cluster','tag',f'cohen_{metric_ranking}','metric_all']]

        to_remove = pd.merge(full_df,new_chosen_tags[['cluster','tag']])[['cluster','appid']].drop_duplicates()
        
        chosen_tags.append(pd.merge(new_chosen_tags,to_remove.groupby('cluster').agg({'appid':'count'}).reset_index(),on='cluster').assign(level=level))

        full_df = full_df[~full_df['appid'].isin(to_remove['appid'].tolist())]
        clusters = full_df[['cluster','appid']].drop_duplicates()

        level+=1
    
    return pd.concat(chosen_tags)


# COMMAND ----------

full_df_all = all_tags.rename(columns={'game_id':'appid'})

names = []

for year in cl['year'].unique() :
    full_df = pd.merge(full_df_all,cl[cl['year']==year][['appid','cluster']],on='appid').drop_duplicates()
    clusters = cl[cl['year']==year][['appid','cluster']].drop_duplicates()
    names.append(construction_iteration(full_df,clusters).assign(year=year))

names = pd.concat(names)   

names['part_representation'] = names.groupby(['year','cluster'])['appid'].cumsum() / names.groupby(['year','cluster'])['appid'].transform('sum')

names = pd.merge(
    names,
    names[names['part_representation']>=0.9].groupby(['year','cluster']).agg({'part_representation':'min'}).rename(columns={'part_representation':'threshold_representation'}).reset_index(),
    on = ['year','cluster']
)

names['is_representant'] = names['part_representation']<=names['threshold_representation']

del names['threshold_representation']


# COMMAND ----------

names.sort_values(['year','cluster']).head(10)

# COMMAND ----------

names

# COMMAND ----------

names_cropped = names[names['is_representant']].groupby(['year','cluster']).agg({'tag':lambda x : ' - '.join(x)}).reset_index()
names_cropped['tag'] = names_cropped['year'].astype(str)+'_'+names_cropped['tag']

# COMMAND ----------

names_cropped

# COMMAND ----------

commonalities_all = pd.merge(
    pd.merge(
        commonalities,
        names_cropped[['year','cluster','tag']].rename(columns={'year':'year_x','cluster':'cluster_x','tag':'name_x'}),
        on=['cluster_x','year_x']),
    names_cropped[['year','cluster','tag']].rename(columns={'year':'year_y','cluster':'cluster_y','tag':'name_y'}),
    on=['cluster_y','year_y'])

# COMMAND ----------

commonalities_all

# COMMAND ----------

# Trier
df_nodes = pd.merge(
    pd.merge(cl,gdco_ref[['appid','year']],on=['year','appid']).groupby(['cluster','year']).agg({'weight':'sum'}).reset_index(),
    names_cropped,
    on = ['cluster','year'])[['year','tag','weight']]

df_nodes.columns = ['year','name','number']

# df_edges : year_from, name_from, year_to, name_to, V

df_edges = commonalities_all[['year_x','name_x','year_y','name_y','appid']]
df_edges.columns = ['year_from', 'name_from', 'year_to', 'name_to', 'V']

# COMMAND ----------

df_nodes

# COMMAND ----------

df_nodes["order"] = (
    df_nodes.groupby("year")["number"]
    .rank(ascending=False, method="first")
)

# clé pratique
df_nodes["key"] = list(zip(df_nodes.year, df_nodes.name))

pos = dict(zip(df_nodes["key"], df_nodes["order"]))

def compute_barycenter(year, direction="up"):
    """
    direction = "up"  : regarde année précédente
    direction = "down": regarde année suivante
    """
    updates = {}

    for (y, name), p in pos.items():
        if y != year:
            continue

        if direction == "up":
            neigh = df_edges[
                (df_edges.year_to == y) & (df_edges.name_to == name)
            ][["year_from", "name_from", "V"]]
        else:
            neigh = df_edges[
                (df_edges.year_from == y) & (df_edges.name_from == name)
            ][["year_to", "name_to", "V"]]

        if len(neigh) == 0:
            updates[(y, name)] = p
            continue

        vals = []
        weights = []

        for _, r in neigh.iterrows():
            key = (r.iloc[0], r.iloc[1])
            if key in pos:
                vals.append(pos[key])
                weights.append(r["V"])

        if vals:
            updates[(y, name)] = np.average(vals, weights=weights)
        else:
            updates[(y, name)] = p

    return updates


# COMMAND ----------

years = sorted(df_nodes.year.unique())

for _ in range(8):  # 5–10 passes suffisent souvent
    # bas → haut
    for y in years[1:]:
        pos.update(compute_barycenter(y, "up"))

    # haut → bas
    for y in reversed(years[:-1]):
        pos.update(compute_barycenter(y, "down"))


# COMMAND ----------

df_nodes["order"] = df_nodes["key"].map(pos)
df_nodes["x"] = (
    df_nodes.groupby("year")["order"]
    .rank(method="first")
)

df_nodes["x"] -= df_nodes.groupby("year")["x"].transform("mean")


# COMMAND ----------

# DBTITLE 1,Untitled
# Y = année (numérique)
df_nodes["y"] = df_nodes["year"]

size_scale = 3000 / df_nodes["number"].max()  # ajuste visuellement
df_nodes["size_plot"] = df_nodes["number"] * size_scale

# COMMAND ----------

# Merge source
df_edges_plot = df_edges.merge(
    df_nodes[["year", "name", "x", "y"]],
    left_on=["year_from", "name_from"],
    right_on=["year", "name"],
    how="left"
).rename(columns={"x": "x_from", "y": "y_from"}).drop(columns=["year", "name"])

# Merge target
df_edges_plot = df_edges_plot.merge(
    df_nodes[["year", "name", "x", "y"]],
    left_on=["year_to", "name_to"],
    right_on=["year", "name"],
    how="left"
).rename(columns={"x": "x_to", "y": "y_to"}).drop(columns=["year", "name"])


# COMMAND ----------

edge_scale = 5 / df_edges_plot["V"].max()
df_edges_plot["linewidth"] = df_edges_plot["V"] * edge_scale
df_edges_plot["alpha"] = 0.1 + 0.9 * (df_edges_plot["V"] / df_edges_plot["V"].max())


# COMMAND ----------

fig, ax = plt.subplots(figsize=(10, 8))

# --- ARÊTES D’ABORD (derrière) ---
for _, row in df_edges_plot.iterrows():
    ax.plot(
        [row["x_from"], row["x_to"]],
        [row["y_from"], row["y_to"]],
        linewidth=row["linewidth"],
        alpha=row["alpha"],
        color="gray",
        zorder=1
    )

# --- BULLES ---
sc = ax.scatter(
    df_nodes["x"],
    df_nodes["y"],
    s=df_nodes["size_plot"],
    alpha=0.8,
    zorder=2
)


import textwrap

def wrap_label(text, width=15):
    return "\n".join(textwrap.wrap(str(text), width=width))

for _, row in df_nodes.iterrows():
    label = wrap_label(row["name"], 15)
    ax.text(
        row["x"],
        row["y"],
        label,
        ha="center",
        va="center",
        fontsize=8,
        linespacing=0.9  # réduit un peu l'espace vertical
    )

# Mise en forme
ax.set_xlabel("")
ax.set_ylabel("Year")
ax.set_title("Flow of names across years")
ax.set_xticks([])  # on cache l’axe X
ax.invert_yaxis()  # première année en bas
plt.tight_layout()
plt.show()


# COMMAND ----------

