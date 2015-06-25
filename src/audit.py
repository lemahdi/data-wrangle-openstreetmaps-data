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


FILE_NAME = "../data/singapore.osm"
TAGS = ["member", "nd", "node", "relation", "tag", "way"]
STREET_TYPES = ["Crescent", "Close", "Drive", "Road", "Avenue", "Terrace", "Park", "Loop", "Street", "View", "Place", "Rise", "Way", "Hill", "Square", "Circle", "Link", "Quay", "Lane", "Boulevard", "Walk", "Green"]
STREET_TYPES_MAP = {"Cresent" : "Crescent", "Rd" : "Road", "Ave" : "Avenue", "Avebue" : "Avenue", "Aenue" : "Avenue", "St" : "Street",
                    "Jalan" : "Road", "Jln" : "Road", "Jl." : "Road", "Jln." : "Road", "Lorong" : "Lane"} # Translations from Indonesian and Malay


def audit_counter():
    auditer = defaultdict(int)
    for event, elem in ET.iterparse(FILE_NAME):
        auditer[elem.tag] += 1
    pprint(auditer)
    with open("../output/audit_counter.txt", "w") as f:
        f.write(json.dumps(auditer, indent=2)+"\n")
    return auditer

def audit_tag():
    auditer = defaultdict(set)
    for event, elem_parent in ET.iterparse(FILE_NAME):
        for elem_child in elem_parent:
            auditer[elem_parent.tag].add(elem_child.tag)
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_tag.txt")
    return auditer

def audit_attrib():
    auditer = defaultdict(set)
    for event, elem in ET.iterparse(FILE_NAME):
        if elem.tag not in TAGS:
            continue
        for attrib in elem.attrib.keys():
            auditer[elem.tag].add(attrib)
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_attrib.txt")
    return auditer

def audit_relation():
    auditer = set()
    for event, elem in ET.iterparse(FILE_NAME):
        if elem.tag == "relation":
            for member in elem:
                if member.tag == "member":
                    auditer.add(member.attrib["type"])
    pprint(auditer)
    with open("../output/audit_relation.txt", "w") as f:
        f.write(str(auditer))
    return auditer

def audit_key(some_re = None, suffix = ""):
    auditer = set()
    for event, elem in ET.iterparse(FILE_NAME):
        if elem.tag == "tag":
            if some_re == None:
                auditer.add(elem.attrib["k"])
            elif some_re.search(elem.attrib["k"]):
                continue
            else:
                auditer.add(elem.attrib["k"])
    pprint(auditer)
    with open("../output/audit_key{0}.txt".format(suffix), "w") as f:
        f.write(str(auditer))
    return auditer

def audit_key_nocolon():
    return audit_key(re.compile(r'.*:.*'), "nocolon")

def audit_key_pbchars():
    return audit_key(re.compile(r'[^=\+/&<>;\'"\?%#$@\,\. \t\r\n]'), "pbchars")

def audit_key_counter():
    colon_re = re.compile(r'.*:.*')
    auditer = defaultdict(int)
    for event, elem in ET.iterparse(FILE_NAME):
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

def audit_key_colon_counter():
    colon_re = re.compile(r'.*:.*')
    auditer = defaultdict(set)
    for event, elem in ET.iterparse(FILE_NAME):
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

def audit_addr_street():
    auditer = defaultdict(set)
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
    for event, elem in ET.iterparse(FILE_NAME):
        if elem.tag=="way" or elem.tag=="node":
            for tag in elem:
                if tag.tag=="tag" and tag.attrib["k"]=="addr:street":
                    value = tag.attrib["v"]
                    street_type = "NULL"

                    if type4_re.search(value): # "Jalan Pemimpin"
                        street_type = type4_re.search(value).group(1).lower().capitalize()
                        street_type = STREET_TYPES_MAP[street_type]
                        street_tail = type4_re.search(value).group(2)
                        value = street_tail + " " + street_type # "Pemimpin Road"
                    elif type1_re.search(value): # "Ang Mo Kio Avenue 10"
                        if type3_re.search(value):
                            s = type3_re.search(value)
                            street_type = s.group(1) # "Avenue"
                            street_nb = s.group(2) # "10"
                            value = street_nb + " " + value.replace(s.group(), "") + " " + street_type
                    elif type2_re.search(value): # "Dover Avenue" or "Admiralty Road West"
                        street_type = type2_re.search(value).group()
                        if type5_re.search(value): # "Admiralty Road West"
                            s = type5_re.search(value)
                            street_type2 = s.group(1) # "Road"
                            street_type2 = street_type2.lower().capitalize()
                            if street_type2 in STREET_TYPES_MAP.keys() or street_type2 in STREET_TYPES:
                                if s.group(2) not in STREET_TYPES_MAP.keys() and s.group(2) not in STREET_TYPES:
                                    street_type = street_type2

                    if street_type in STREET_TYPES_MAP.keys(): # "Ave"
                        street_type = STREET_TYPES_MAP[street_type] # "Avenue"
                    street_type = street_type.lower().capitalize()
                    if street_type in STREET_TYPES:
                        auditer[street_type].add(value)
                    else:
                        auditer["bad"].add(value)
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_addr_street.txt")
    return auditer

def audit_addr_postcode():
    auditer = defaultdict(set)
    type5_re = re.compile(r'.*([\d]{5})')
    type6_re = re.compile(r'.*([\d]{6})')
    for event, elem in ET.iterparse(FILE_NAME):
        if elem.tag=="way" or elem.tag=="node":
            for tag in elem:
                if tag.tag=="tag" and tag.attrib["k"]=="addr:postcode":
                    value = tag.attrib["v"]
                    match = type6_re.search(tag.attrib["v"])
                    if match:
                        value = match.group(1)
                        auditer["good"].add(value)
                        continue
                    match = type5_re.search(value)
                    if match:
                        value = "0" + match.group(1)
                        auditer["good"].add(value)
                        continue
                    auditer["bad"].add(value)
    pprint(auditer)
    dump_dicosets(auditer, "../output/audit_addr_postcode.txt")
    return auditer

def audit_user():
    auditer = set()
    for event, elem in ET.iterparse(FILE_NAME):
        if "user" in elem.attrib.keys():
            auditer.add(elem.attrib["user"])
    pprint(auditer)
    with open("../output/audit_user", "w") as f:
        f.write(str(auditer))
    return auditer
