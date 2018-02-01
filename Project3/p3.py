'''
# Extract a sample using the code provided in the project notes

OSM_FILE = "seattle_washington.osm"
SAMPLE_FILE = "sample.osm"

k = 200  # Parameter: take every k-th top level element


def get_element(osm_file, tags=('node', 'way', 'relation')):
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write(b'<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write(b'</osm>')
'''

#************************************************************************************

# First, we'll import the needed libraries and define needed regular expressions

# Importing needed libraries
import re
from collections import defaultdict
import xml.etree.cElementTree as ET
import cerberus
import schema
import csv
import codecs

# Loading files
OSMFILE = "seattle_washington.osm"

# Defining needed regular expressions
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'(\b\S+\.?$)', re.IGNORECASE)
street_direc_re = re.compile(r'\b(N|S|W|E|NE|NW|SE|SW)\b')
# Washington post code starts with 98
postcode_re = re.compile(r'98[0-9]{3}')

# Defining needed variables
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Way", "Crescent", "Highway", "Ridge", "Terrace",
            "Heights", "Point", "Loop", "Esplanade", "Circle", "Walk", "Broadway", "Crest", "Close",
            "Main Street", "Island", "Driveway", "Trail"]

mapping = {"St": "Street",
           "St.": "Street",
           "st": "Street",
           "ST": "Street",
           "street": "Street",
           "Stree": "Street",
           "Ave": "Avenue",
           "Av.": "Avenue",
           "Ave.": "Avenue",
           "av.": "Avenue",
           "avenue": "Avenue",
           "AVE": "Avenue",
           "Rd.": "Road",
           "Rd": "Road",
           "RD": "Road",
           "MainStreet": "Main Street",
           "Dr": "Drive",
           "Blvd": "Boulevard",
           "Blvd.": "Boulevard",
           "Pl": "Place",
           "Hwy": "Highway",
           "lane": "Lane",
           "driveway": "Driveway",


           "S": "South",
           "N": "North",
           "W": "West",
           "E": "East",
           "NE": "Northeast",
           "NW": "Northwest",
           "SE": "Southeast",
           "SW": "Southwest"
           }
directions = ["South", "North", "West", "East", "Northeast", "Northwest", "Southeast", "Southwest"]


# Part 1: Auditing the map
# Needed functions

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def is_postcode(elem):
    return (elem.attrib['k'] == "addr:postcode")



# function to fix direction abbreviation problem
def audit_directions(street_name):
    m = street_direc_re.search(street_name)
    if m:
        direc = m.group()
        start = m.start()
        # ensure the replacement happens only once & in the right place
        street_name = street_name[:start] + street_name[start:].replace(direc, mapping[direc], 1)

    return street_name

# function to store street types
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if (street_type in directions):
            new_add = street_name.replace(street_type, '').strip()
            m = street_type_re.search(new_add)
            if m:
                street_type = m.group()

        street_types[street_type].add(street_name)

    return street_name


# function to extract postcodes (fix postcode problem)
def audit_postcode(postcode):
    m = postcode_re.search(postcode)
    if m:
        postcode = m.group()

    return postcode


# function to fix street names
def update_name(name):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        if street_type in directions:
            new_add = name.replace(street_type, '').strip()
            m = street_type_re.search(new_add)
            if m:
                street_type = m.group()
                if street_type not in expected:
                    if street_type in mapping.keys():
                        name = name.replace(street_type, mapping[street_type])
        elif street_type not in expected:
            if street_type in mapping.keys():
                name = name.replace(street_type, mapping[street_type])

    return name


# Main function for auditing the file
def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    # fix direction abbreviations first
                    tag.attrib['v'] = audit_directions(tag.attrib['v'])
                    # then fix street name abbreviations
                    audit_street_type(street_types, tag.attrib['v'])
                    tag.attrib['v'] = update_name(tag.attrib['v'])
                elif is_postcode(tag):
                    # fix postcode
                    tag.attrib['v'] = audit_postcode(tag.attrib['v'])

    osm_file.close()

    return street_types

# call auditing function
audit(OSMFILE)


#Part 2: Overview and exploration

# function to find the number of unique users
def unique_users(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        id = element.get('uid')
        if id is not None:
            users.add(id)

    return len(users)


# function to get the top ten contributing users
def top_users(filename):
    users = {}
    for _, element in ET.iterparse(filename):
        if element.get('user') is not None:
            if element.get('user') in users:
                users[element.get('user')] += 1
            else:
                users[element.get('user')] = 1

    top = list(users.values())
    total = sum(top)
    top.sort()
    top = top[-10:]

    top_ten = {}
    for k, v in users.items():
        if v in top:
            top_ten[k] = round((v/total)*100, 2)

    return sorted(top_ten.items(), key=lambda x: x[1], reverse=True)

# calling previous functions
print('The number of unique users: '+str(unique_users(OSMFILE)))
print('Top contributing users: ')
print(top_users(OSMFILE))


# tags distribution (Recording tag names along with counting their appearance)
def count_tags(filename):
    tags ={}
    for event, element in ET.iterparse(filename):
        if (element.tag in tags):
            tags[element.tag] +=1
        else:
            tags[element.tag] = 1
    return tags

# Call function
print (count_tags(OSMFILE))


# Part 3: Writing files as csv files

# Output files
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

SCHEMA = schema.schema

# schema order
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS, default_tag_type='regular'):
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':

        # getting attributes
        node_attribs['id'] = element.attrib['id']
        node_attribs['user'] = element.attrib.get('user')
        node_attribs['uid'] = element.attrib.get('uid')
        node_attribs['version'] = element.attrib.get('version')
        node_attribs['lat'] = element.attrib.get('lat')
        node_attribs['lon'] = element.attrib.get('lon')
        node_attribs['timestamp'] = element.attrib.get('timestamp')
        node_attribs['changeset'] = element.attrib.get('changeset')

        # getting tags
        tags = get_tags(element)

        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':

        # getting attributes
        way_attribs['id'] = element.attrib['id']
        way_attribs['user'] = element.attrib['user']
        way_attribs['uid'] = element.attrib['uid']
        way_attribs['version'] = element.attrib['version']
        way_attribs['timestamp'] = element.attrib['timestamp']
        way_attribs['changeset'] = element.attrib['changeset']

        # getting nodes
        counter = 0
        for node in element.iter('nd'):
            way_node_attribs = {}
            way_node_attribs['id'] = element.attrib['id']
            way_node_attribs['node_id'] = node.attrib['ref']
            way_node_attribs['position'] = counter
            counter += 1

            way_nodes.append(way_node_attribs)

        # getting tags
        tags = get_tags(element)

        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# tag function
def get_tags(element):
    tags = []
    for tag in element.iter('tag'):
        tag_attribs = {}

        tag_attribs['id'] = element.attrib['id']

        key = tag.attrib['k']
        if (problem_chars.search(key)):
            break
        elif (lower_colon.search(key)):
            tag_attribs['type'] = key.split(':', 1)[0]
            tag_attribs['key'] = key.split(':', 1)[1]
        else:
            tag_attribs['key'] = key
            tag_attribs['type'] = 'regular'

        tag_attribs['value'] = tag.attrib['v']

        tags.append(tag_attribs)

    return tags


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        print (type(validator.errors))
        field, errors = next(validator.errors.items())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            # utf-8 encoding resulted in format error in the written files, thus I removed it
            k: v for k, v in row.items()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)



# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, codecs.open(
            WAYS_PATH, 'w') as ways_file, codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, codecs.open(WAY_TAGS_PATH,
                                                                                                          'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)


        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


process_map(OSMFILE, validate=False)
print ('Done writing files! Yay ;)')

