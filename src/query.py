#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from pymongo import MongoClient
from bson.objectid import ObjectId
from pprint import pprint
import codecs
import json


# initialize db
def get_db():
    from pymongo import MongoClient
    client = MongoClient('localhost:27017')
    db = client.p2_data_wrangling
    return db


# update to GeoJSON coordinates
def update_pos(db):
    spore = db.singapore
    for doc in spore.find():
        if (type(doc["pos"]) != list):
            continue

        spore.update({ "_id" : doc["_id"] },
                      { "$set" : {
                            "pos" : {
                                "type" : "Point",
                                "coordinates" : doc["pos"]
                            }
                      } })

# update lat/lon order
def update_latlon(db):
    spore = db.singapore
    for doc in spore.find():
        doc["pos"]["coordinates"].reverse()
        spore.update({ "_id" : doc["_id"] },
                      { "$set" : {
                            "pos" : {
                                "type" : "Point",
                                "coordinates" : doc["pos"]["coordinates"]
                            }
                      } })

# most active users
def most_active_users(db):
    pipeline = [ { "$group" : { "_id" : "$created.user",
                                "count" : { "$sum" : 1 } } },
                 { "$sort" : { "count" : -1 } },
                 { "$limit" : 10 } ]
    return db.singapore.aggregate(pipeline)

# area with most restaurants
def nearest_toilet(db, restaurant_id, max_distance=None):
    query = { "_id" : ObjectId(restaurant_id) }
    resto = db.singapore.find_one(query)
    query = { "pos" : 
                { "$near" : 
                    { "$geometry" : 
                        { "type" : "Point",
                          "coordinates" : resto["pos"]["coordinates"] }
                    }
                },
                "amenity" : { "$regex" : "toilet", "$options" : "i" }
            }
    if max_distance:
        query["pos"]["$near"]["$maxDistance"] = max_distance # in meters
    toilets = db.singapore.find(query).limit(10)
    with codecs.open("../output/nearest_toilets_for_{0}".format(resto["_id"]), "w") as fo:
        for toilet in toilets:
            pprint(toilet)
            toilet["_id"] = str(toilet["_id"])
            fo.write(json.dumps(toilet, indent=2) + "\n")
    return toilets
# extreme coordinates
def extrems(db, min_or_max, lon_or_lat):
    if min_or_max not in ["min", "max"]:
        return None
    if lon_or_lat not in ["longitude", "latitude"]:
        return None
    minmax = -1
    if min_or_max == "min":
        minmax = 1
    lonlat = 0
    if lon_or_lat == "latitude":
        lonlat = 1
    pipeline = [ { "$project" : { lon_or_lat : "$pos.coordinates[{0}]".format(str(lonlat)) } },
                 { "$sort" : { lon_or_lat : minmax } },
                 { "$limit" : 1 } ]
    c = db.singapore.aggregate(pipeline)
    return c
    #return db.singapore.find_one( { "_id" : c.next()["_id"] } )
