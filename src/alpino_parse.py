# functions used to parse and analyze the given questions
# also retreive the corresponding wikiPageID for each Concept (/object)

import socket
from lxml import etree
from exception_classes import *

def parse_question(question, host='zardoz.service.rug.nl', port=42424):
    """
    Analyseert de gestelde vraag tot op het niveau van het concept en de eigenschap in natuurlijke taal, met hulp van
    Alpino voor het parsen van de vraag.

    :param question: De door de gebruiker gestelde vraag als string.
    :return: de parse als XML.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    question += "\n\n"
    question_bytes = question.encode('utf-8')
    s.sendall(question_bytes)
    bytes_received = b''
    while True:
        byte = s.recv(8192)
        if not byte:
            break
        bytes_received += byte
    xml = etree.fromstring(bytes_received)
    return xml

def analyze_question(xml):
    """
    Probeert concept en eigenschap uit een vraag in natuurlijke taal te filteren met behulp van een parse van Alpino.

    :param parsed_q: de parse uit Alpino in XML.
    :return: het concept en de bijbehorende eigenschap in een Tuple.
    """
    # TODO: Uitbreiden verkrijgen concept
    identity = []
    names = xml.xpath('//node[@rel="obj1" and @ntype="eigen"] | //node[@spectype="deeleigen"] | //node[@rel="su" and @ntype="eigen"]')
    for name in names:
        identity.append(name.attrib["word"])
    Concept = " ".join(identity)

    # Check if we've found a concept
    if len(Concept) == 0:
        raise NoConceptException


    # TODO: Uitbreiden verkrijgen eigenschap
    relation = []
    properties = xml.xpath('//node[@pos="adj" and @rel="mod"] | //node[@rel="hd" and @pos="noun"] | //node[@rel="vc"]/node[@rel="hd"]')
    vraagwoorden = xml.xpath('//node[(@rel="whd" and (@root="wanneer" or @root="waar")) or (@rel="det" and @root="hoeveel")]')
    for prop in properties:
        relation.append(prop.attrib["word"])
    for vraagwoord in vraagwoorden:
        word = (vraagwoord.attrib["word"]).lower()
        if word == "wanneer" or word == "waar" or word == "hoeveel":
            relation = [word] + relation
    Property = " ".join(relation)

    # Check if we've found a property
    if len(Property) == 0:
        raise NoPropertyException

    return Concept, Property

def find_resource(Concept, anchors):
    resource_id = find_wikiID(Concept, anchors)
    if resource_id is None:
        resource_id = "?" + Concept
    return resource_id

def find_wikiID(Concept, anchors):
    """
    Probeert het juiste Wikipedia ID bij een bepaald concept te vinden. Gebruikt hiervoor zowel page.csv als
    anchor_summary.csv.

    :param concept: het concept als string.
    :return: Wikipedia ID als string.
    """
    # TODO: Verkrijg Wikipedia ID met behulp van page.csv én anchor_summary.csv
    count = 0
    wikiID = None
    for row in anchors:
        if row[0].lower() == Concept.lower():
            # Get all possible references for the concept
            possiblePages = (row[1].strip('"')).split(";")

            # Get the ID of the most frequently referenced page
            wikiIDtemp = (possiblePages[0].split(":"))[0]
            wikiIDfreq = int((possiblePages[0].split(":"))[1])
            if wikiIDfreq > count:
                count = wikiIDfreq
                wikiID = wikiIDtemp

    return wikiID