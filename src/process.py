#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import xml.etree.cElementTree as ET
import json
import codecs
import re
from audit import process_addr
from audit import process_postcode


OSM_FILE = "../data/singapore.osm"
JSON_FILE = "../output/singapore.json"

pb_chars_re = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


# clean addresses and post codes
def clean_tags(element):
    new_tag = {}
    for tag in element.iter("tag"):
        attrib = tag.attrib["k"]
        value = tag.attrib["v"]
        if pb_chars_re.search(attrib):
            continue

        if attrib == "addr:street":
            addr = process_addr(value)
            if addr["status"]:
                new_tag["address"] = {}
                new_tag["address"]["street"] = addr["new_value"]
                new_tag["address"]["type"] = addr["type"]
                if "housenumber" in addr.keys() and "housenumber" not in new_tag.keys():
                    new_tag["housenumber"] = addr["housenumber"]

        elif attrib == "addr:postcode":
            postcode = process_postcode(value)
            if "address" not in new_tag.keys():
                new_tag["address"] = {}
            if postcode["status"]:
                new_tag["address"]["postcode"] = postcode["new_value"]

        else:
            new_tag[attrib] = value

    return new_tag

# processing nodes and ways
def process_elem(element):
    if element.tag == "node" or element.tag == "way" :
        # intialisation
        node = {"id" : element.attrib["id"],
                "type" : element.tag,
                "created" : {},
                "pos" : [None, None] }
        # processing attributes
        for attr in element.attrib.keys():
            value = element.attrib[attr]
            if attr in CREATED:
                node["created"][attr] = value
            elif attr == "lat":
                node["pos"][0] = float(value)
            elif attr == "lon":
                node["pos"][1] = float(value)
            else:
                node[attr] = value
        # processing tags
        node.update(clean_tags(element))
        # only "way"
        if element.tag == "way":
            node["node_refs"] = []
            for nd in element.iter("nd"):
                node["node_refs"].append(nd.attrib["ref"])
        return node
    else:
        return None

# processing the whole map
def process_map(pretty = False):
    data = []
    with codecs.open(JSON_FILE, "w") as fo:
        for _, element in ET.iterparse(OSM_FILE):
            el = process_elem(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2) + "\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data
