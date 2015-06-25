#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import xml.etree.cElementTree as ET
from collections import defaultdict
from pprint import pprint
import json
import re
import operator


def dump_dicosets(dico, filename):
    d = {}
    for k, v in dico.items():
        d[k] = list(v)
    with open(filename, "w") as f:
        f.write(json.dumps(d, indent=2)+"\n")


OSM_FILE = "../data/singapore.osm"
TAGS = ["member", "nd", "node", "relation", "tag", "way"]
STREET_TYPES = ["Crescent", "Close", "Drive", "Road", "Avenue", "Terrace", "Park", "Loop", "Street", "View", "Place", "Rise", "Way", "Hill", "Square", "Circle", "Link", "Quay", "Lane", "Boulevard", "Walk", "Green"]
STREET_TYPES_MAP = {"Cresent" : "Crescent", "Rd" : "Road", "Ave" : "Avenue", "Avebue" : "Avenue", "Aenue" : "Avenue", "St" : "Street",
                    "Jalan" : "Road", "Jln" : "Road", "Jl." : "Road", "Jln." : "Road", "Lorong" : "Lane"} # Translations from Indonesian and Malay


# count the number of appearance of each tag
def audit_counter():
    auditer = defaultdict(int)
    for event, elem in ET.iterparse(OSM_FILE):
        auditer[elem.tag] += 1
    pprint(auditer)
    with open("../output/audit_counter.txt", "w") as f:
        f.write(json.dumps(auditer, indent=2)+"\n")
    return auditer

# display direct inner tags for each tag
def audit_tag():
    auditer = defaultdict(set)
    for event, elem_parent in ET.iterparse(OSM_FILE):
        for elem_child in elem_parent:
            auditer[elem_parent.tag].add(elem_child.tag)
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_tag.txt")
    return auditer

# display attributes in each tag
def audit_attrib():
    auditer = defaultdict(set)
    for event, elem in ET.iterparse(OSM_FILE):
        if elem.tag not in TAGS:
            continue
        for attrib in elem.attrib.keys():
            auditer[elem.tag].add(attrib)
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_attrib.txt")
    return auditer

# diplay tag types within the tag relation
def audit_relation():
    auditer = set()
    for event, elem in ET.iterparse(OSM_FILE):
        if elem.tag == "relation":
            for member in elem:
                if member.tag == "member":
                    auditer.add(member.attrib["type"])
    pprint(auditer)
    with open("../output/audit_relation.txt", "w") as f:
        f.write(str(auditer))
    return auditer

# display values of the attribute k for all tags
def audit_key(some_re = None, suffix = ""):
    auditer = set()
    for event, elem in ET.iterparse(OSM_FILE):
        if elem.tag == "tag":
            if some_re == None:
                auditer.add(elem.attrib["k"])
            elif some_re.search(elem.attrib["k"]):
                continue
            auditer.add(elem.attrib["k"])
    pprint(auditer)
    with open("../output/audit_key{0}.txt".format(suffix), "w") as f:
        f.write(str(auditer))
    return auditer

# display values of the attribute k without colons for all tags
def audit_key_nocolon():
    return audit_key(re.compile(r'.*:.*'), "nocolon")

# display values of the attribute k without problematic characters for all tags
def audit_key_pbchars():
    return audit_key(re.compile(r'[^=\+/&<>;\'"\?%#$@\,\. \t\r\n]'), "pbchars")

# display number of appearance of each key in all tags
def audit_key_counter():
    colon_re = re.compile(r'.*:.*')
    auditer = defaultdict(int)
    for event, elem in ET.iterparse(OSM_FILE):
        if elem.tag == "tag":
            key = elem.attrib["k"]
            if colon_re.search(key):
                key = key.split(":")[0]
            auditer[key] += 1
    auditer = sorted(auditer.items(), key=operator.itemgetter(1), reverse=True)
    pprint(auditer)
    with open("../output/audit_key_counter.txt", "w") as f:
        f.write(json.dumps(auditer, indent=2)+"\n")
    return auditer

# display number of appearance of each key with a colon and its suffixes in all tags
def audit_key_colon_counter():
    colon_re = re.compile(r'.*:.*')
    auditer = defaultdict(set)
    for event, elem in ET.iterparse(OSM_FILE):
        if elem.tag == "tag":
            key = elem.attrib["k"]
            if colon_re.search(key):
                keys = key.split(":")
                [auditer[keys[0]].add(k) for k in keys[1:]]
    new_auditer = {}
    for k, v in auditer.items():
        new_auditer[k] = {}
        new_auditer[k]["count"] = len(v)
        new_auditer[k]["sub_keys"] = list(v)
    pprint(new_auditer)
    with open("../output/audit_key_colon_counter", "w") as f:
        f.write(json.dumps(new_auditer, indent=2)+"\n")
    return new_auditer

# filter incorrect street names, and clean correct street names
# ending with numbers: "Neo Tiew Lane 3"
type1_re = re.compile(r'[#\-\d]+\.?$')
# ending with non-white space characters: 
type2_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
# extracting last word: "Neo Tiew (Lane) (3)"
type3_re = re.compile(r'\s?(\w+)\s([#\-\d]+)\.?$', re.IGNORECASE)
# special translation
type4_re = re.compile(r'.*\b(jalan|lorong|jln\.?|jl\.?)\s(.+)$', re.IGNORECASE)
# street type is not the last word, but step-last
type5_re = re.compile(r'\s?(\w+)\s(\w+)\.?$', re.IGNORECASE)
def process_addr(value):
    addr = { "value" : value, "status" : False }
    street_type = "NULL"
    new_value = value

    if type4_re.search(value): # "Jalan Pemimpin"
        street_type = type4_re.search(value).group(1).lower().capitalize()
        street_type = STREET_TYPES_MAP[street_type]
        street_tail = type4_re.search(value).group(2)
        new_value = street_tail + " " + street_type # "Pemimpin Road"
    elif type1_re.search(value): # "Ang Mo Kio Avenue 10"
        if type3_re.search(value):
            s = type3_re.search(value)
            street_type = s.group(1) # "Avenue"
            street_nb = s.group(2) # "10"
            new_value = street_nb + " " + value.replace(s.group(), "") + " " + street_type # "10 Ang Mo Kio Avenue"
    elif type2_re.search(value): # "Dover Avenue" or "Admiralty Road West"
        street_type = type2_re.search(value).group()
        if type5_re.search(value): # "Admiralty Road West"
            s = type5_re.search(value)
            street_type2 = s.group(1).lower().capitalize() # "Road"
            if street_type2 in STREET_TYPES_MAP.keys() or street_type2 in STREET_TYPES:
                if s.group(2) not in STREET_TYPES_MAP.keys() and s.group(2) not in STREET_TYPES: # to prevent such cases ".. Park Road"
                    street_type = street_type2

    if street_type in STREET_TYPES_MAP.keys(): # "Ave"
        street_type = STREET_TYPES_MAP[street_type] # "Avenue"
    street_type = street_type.lower().capitalize()
    if street_type in STREET_TYPES:
        addr["type"] = street_type
        addr["status"] = True
        addr["new_value"] = new_value
    return addr

def audit_addr_street():
    auditer = defaultdict(set)
    for event, elem in ET.iterparse(OSM_FILE):
        if elem.tag=="way" or elem.tag=="node":
            for tag in elem:
                if tag.tag=="tag" and tag.attrib["k"]=="addr:street":
                    addr = process_addr(tag.attrib["v"])
                    auditer[addr["status"]].add(addr["value"])
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_addr_street.txt")
    return auditer

# filter incorrect postcodes, and clean correct postcodes
# 5-digits post codes
type6_re = re.compile(r'[^\d]*([\d]{5})$')
# 6-digits post codes
type7_re = re.compile(r'[^\d]*([\d]{6})$')
def process_postcode(value):
    postcode = { "value" : value, "status" : False }
    new_value = value

    match = type7_re.search(value)
    if match:
        postcode["new_value"] = match.group(1)
        postcode["status"] = True
        return postcode
    match = type6_re.search(value)
    if match:
        postcode["new_value"] = "0" + match.group(1)
        postcode["status"] = True
        return postcode
    return postcode

def audit_addr_postcode():
    auditer = defaultdict(set)
    for event, elem in ET.iterparse(OSM_FILE):
        if elem.tag=="way" or elem.tag=="node":
            for tag in elem:
                if tag.tag=="tag" and tag.attrib["k"]=="addr:postcode":
                    postcode = process_postcode(tag.attrib["v"])
                    auditer[postcode["status"]].add(postcode["value"])
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_addr_postcode.txt")
    return auditer

# diplay all users
def audit_user():
    auditer = set()
    for event, elem in ET.iterparse(OSM_FILE):
        if "user" in elem.attrib.keys():
            auditer.add(elem.attrib["user"])
    pprint(auditer)
    with open("../output/audit_user", "w") as f:
        f.write(str(auditer))
    return auditer
