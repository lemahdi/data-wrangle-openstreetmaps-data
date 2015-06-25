#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import xml.etree.cElementTree as ET
from collections import defaultdict
from pprint import pprint
import re
from audit import process_addr
from audit import process_postcode


OSM_FILE = "../data/singapore.osm"


# clean addresses and post codes
def clean_tags(elem):
    for tag in elem:
        attrib = tag.attrib["k"]
        if tag.tag=="tag":
            value = tag.attrib["v"]
            if attrib == "addr:street":
                addr = process_addr(value)
            elif attrib == "addr:postcode":
                postcode = process_postcode(value)
