from flask import Flask,render_template, request, url_for
import mysql.connector
import numpy as np
import pandas as pd
import re
from sklearn.preprocessing import MaxAbsScaler
from sklearn.neighbors import NearestNeighbors
import matplotlib.pyplot as plt


app = Flask(__name__,template_folder='Templates',static_folder='Static')



df = pd.read_csv('rating.csv')
anime = pd.read_csv('anime.csv')

anime.loc[(anime["genre"]=="Hentai") & (anime["episodes"]=="Unknown"),"episodes"] = "1"
anime.loc[(anime["type"]=="OVA") & (anime["episodes"]=="Unknown"),"episodes"] = "1"
anime.loc[(anime["type"] == "Movie") & (anime["episodes"] == "Unknown")] = "1"
known_animes = {"Naruto Shippuuden":500, "One Piece":784,"Detective Conan":854, "Dragon Ball Super":86,
                "Crayon Shin chan":942, "Yu Gi Oh Arc V":148,"Shingeki no Kyojin Season 2":25,
                "Boku no Hero Academia 2nd Season":25,"Little Witch Academia TV":25}
for k,v in known_animes.items():
    anime.loc[anime["name"]==k,"episodes"] = v
anime["episodes"] = anime["episodes"].map(lambda x:np.nan if x=="Unknown" else x)

anime["episodes"].fillna(anime["episodes"].median(),inplace = True)
anime["rating"] = anime["rating"].astype(float)
anime["rating"].fillna(anime["rating"].median(),inplace = True)

pd.get_dummies(anime[["type"]]).head()
anime["members"] = anime["members"].astype(float)

anime_features = pd.concat([anime["genre"].str.get_dummies(sep=","),pd.get_dummies(anime[["type"]]),anime[["rating"]],anime[["members"]],anime["episodes"]],axis=1)
anime["name"] = anime["name"].map(lambda name:re.sub('[^A-Za-z0-9]+', " ", name))

max_abs_scaler = MaxAbsScaler()
anime_features = max_abs_scaler.fit_transform(anime_features)

nbrs = NearestNeighbors(n_neighbors=6, algorithm='ball_tree').fit(anime_features)
distances, indices = nbrs.kneighbors(anime_features)

def get_index_from_name(name):
    return anime[anime["name"]==name].index.tolist()[0]

all_anime_names = list(anime.name.values)
def get_id_from_partial_name(partial):
    for name in all_anime_names:
        if partial in name:
            print(name,all_anime_names.index(name))
""" print_similar_query can search for similar animes both by id and by name. """

def print_similar_animes(query=None,id=None):
    list1 = []
    if id:
        for id in indices[id][1:]:
            print(anime.iloc[id]["name"])
    if query:
        found_id = get_index_from_name(query)
        for id in indices[found_id][1:]:
            list1.append(anime.iloc[id]["name"])
        return list1

from mysql.connector import (connection)

cnx = connection.MySQLConnection(user='root', password='admin',host='127.0.0.1',database='Mysql')

cursor = cnx.cursor()

query = ("SELECT user_name, user_pwd FROM sys.login_master")

cursor.execute(query)
output = cursor.fetchall()



@app.route('/',methods=['POST','GET'])
def home():
    return render_template('index.html')

@app.route('/predict',methods=['POST','GET'])
def predict():
    if request.method == 'GET':
        return render_template('predicting.html')
    if request.method == 'POST':
        p = request.form.get("anime")
        prediction = print_similar_animes(p)
        return prediction
    return render_template('predicting.html')

@app.route('/login_validation',methods = ['POST'])
def login_validation():
    flag = 0
    uname = request.form.get('uname')
    pword = request.form.get('pword')
    li = (uname,pword)
    for i in output:
        if (li == i):
            flag = 1
    #return "the uname is {} and password is {}".format(uname,pword)
    if flag == 1:
        return render_template('predicting.html')
    else:
        return ('login invalid')

cursor.close()
cnx.close()
if __name__ == '__main__':
    app.run(debug = True)
