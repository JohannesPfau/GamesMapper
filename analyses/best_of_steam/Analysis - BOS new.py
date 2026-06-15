# Databricks notebook source
# MAGIC %pip install jinja2

# COMMAND ----------

import glob
import pandas as pd
import re

# COMMAND ----------

files = glob.glob("best_of_steam_new*.txt")

# COMMAND ----------

def parse_file(file) :

    year = int(file.split("_")[-1].split(".")[0])

    pattern = re.compile(r'^/(\d+)/')

    ids = []

    id_ligne = 0

    with open(file, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            match = pattern.match(line)
            if match:
                number = int(match.group(1))
                ids.append((id_ligne, number,year))
                id_ligne+=1

    return pd.DataFrame(ids,columns=['id','appid','year'])
    

# COMMAND ----------

all_games = pd.concat([parse_file(file) for file in files])

all_games = all_games.groupby(['appid','year']).agg({'id':'min'}).reset_index().sort_values(['year','id'])
all_games['id'] = 1+all_games.groupby(['year'])['id'].cumcount()

# COMMAND ----------

all_games.groupby('year').agg({'appid':'nunique'})

# COMMAND ----------

gdco = spark.table('rnd_dev.silver.gdco_reference').toPandas()
gdco = gdco[gdco.groupby('appid')['name'].transform('cumcount')==0][['appid','name']].set_index('appid')

gdco.loc[1190460,'name'] = 'Death Stranding'

gdco = gdco.reset_index()




# COMMAND ----------

all_games_gdco = pd.merge(all_games,gdco, on = 'appid',how = 'left')

display(all_games_gdco.groupby('year').agg({'name':'nunique'}))
all_games_gdco[all_games_gdco['name'].isnull()]



# COMMAND ----------

pd.merge(all_games,all_games,on = ['appid']).groupby(['year_x','year_y']).agg({'appid':'count'})['appid'].unstack(level=-1).fillna(0).style.background_gradient()

# COMMAND ----------

all_games_gdco.to_csv('bos_new_2019_2025.csv',index=False)

# COMMAND ----------

