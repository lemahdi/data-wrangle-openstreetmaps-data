#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import xml.etree.cElementTree as ET
import json
from pprint import pprint
import codecs


OSM_FILE = "../data/singapore.osm"
JSON_FILE = "../output/singapore.json"


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def process_map(pretty = False):
    data = []
    with codecs.open(JSON_FILE, "w") as fo:
        for _, element in ET.iterparse(OSM_FILE):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node["id"] = element.attrib["id"]
        node["type"] = element.tag
        node["created"] = {}
        node["pos"] = []
        for attr in element.attrib.keys():
            value = element.attrib[attr]
            if attr in CREATED:
                node["created"][attr] = value
            elif attr == "lat":
                if len(node["pos"]) == 1:
                    lon = node["pos"][0]
                    node["pos"][0] = float(value)
                    value = lon
                node["pos"].append(float(value))
            elif attr == "lon":
                node["pos"].append(float(value))
            else:
                node[attr] = value
        for tag in element.iter("tag"):
            k = tag.attrib["k"]
            if problemchars.match(k):
                continue
            if k.startswith("addr:") and lower_colon.match(k):
                if "address" not in node.keys():
                    node["address"] = {}
                k = k[5:]
                node["address"][k] = tag.attrib["v"]
            elif not k.startswith("addr:"):
                node[k] = tag.attrib["v"]
        if element.tag == "way":
            node["node_refs"] = []
            for nd in element.iter("nd"):
                node["node_refs"].append(nd.attrib["ref"])
        return node
    else:
        return None