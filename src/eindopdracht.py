# Taaltechnologie - Eindopdracht
# taaltech_vooruit
#!/usr/bin/env python3

from SPARQLWrapper import SPARQLWrapper, JSON
from lxml import etree
from datetime import datetime
import csv
import socket
import sys


def main(question, anchors):
    source_DBPedia = "http://nl.dbpedia.org/sparql"

    # Parse and analyze question
    parse = parse_question(question)
    try:
        Concept, Property = analyze_question(parse)

        # Find relevant information for query
        # # Concept
        wikiID = find_resource(Concept, anchors)

        # # Property
        relation = find_relation(Property)

        # Retrieve answer
        answer = query(source_DBPedia, construct_query(wikiID, relation))
        output(answer)

    except NoConceptException:
        # TODO: Meaningful error handling
        print("No Concept")
    except NoPropertyException:
        # TODO: Meaningful error handling
        print("No Property")
    except NoConceptIDException:
        # TODO: Meaningful error handling
        print("No wikiPageID")
    except NoPropertyRelationException:
        # TODO: Meaningful error handling
        print("No relation")
    except NoResultException:
        # TODO: Meaningful error handling
        print("No results")

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
    for prop in properties:
        relation.append(prop.attrib["word"])
    Property = " ".join(relation)

    # Check if we've found a property
    if len(Property) == 0:
        raise NoPropertyException

    return Concept, Property


def find_resource(Concept, anchors):
    resource_id = find_wikiID(Concept, anchors)
    if resource_id is None:
        raise NoConceptIDException
    return resource_id


def find_wikiID(Concept, anchors):
    """
    Probeert het juiste Wikipedia ID bij een bepaald concept te vinden. Gebruikt hiervoor zowel page.csv als
    anchor_summary.csv.

    :param concept: het concept als string.
    :return: Wikipedia ID als string.
    """
    # TODO: Verkrijg Wikipedia ID met behulp van page.csv én anchor_summary.csv
    for row in anchors:
        if row[0] == '{}'.format(Concept):
            # Get all possible references for the concept
            possiblePages = (row[1].strip('"')).split(";")

            # Get the ID of the most frequently referenced page
            wikiID = (possiblePages[0].split(":"))[0]
            return wikiID
    return None

def find_relation(Property):
    """
    Probeert de passende relatie bij een bepaalde eigenschap te vinden. Gebruikt hiervoor zowel een basisset
    eigenschappen als een bestand met synoniemen, op basis waarvan eigenschappen kunnen worden verkregen.

    :param propert: de eigenschap als string.
    :return: de geschikte relatie als
    """
    relations = {
        "geboortedatum": "?identity dbpedia-owl:birthDate ?result",
        "volledige naam": "?identity prop-nl:volledigeNaam ?result",
        "leden": "?identity dbpedia-owl:bandMember ?bandMember . ?bandMember prop-nl:naam ?result",
        "voormalige leden": "?identity dbpedia-owl:formerBandMember ?bandMember . ?bandMember prop-nl:naam ?result",
        "website": "?identity prop-nl:website ?result",
        "beroep": "?identity prop-nl:beroep ?result",
        "bezetting": "?identity prop-nl:functie ?bandMember . ?bandMember rdfs:label ?result",
        "functie": "?identity prop-nl:functie ?bandMember . ?bandMember rdfs:label ?result",
        "functies": "?identity prop-nl:functie ?bandMember . ?bandMember rdfs:label ?result",
        "oorsprong": "?identity dbpedia-owl:origin ?origin . ?origin dbpedia-owl:name ?result",
        "geboren": "?identity dbpedia-owl:birthDate ?result",
        "samengesteld": "?identity prop-nl:functie ?bandMember . ?bandMember rdfs:label ?result",
        "verjaardag" 		: "?identity dbpedia-owl:birthDate ?result",
        "overlijdensdatum" 	: "?identity dbpedia-owl:deathDate ?result",
        "bijnaam" 			: "?identity prop-nl:bijnaam ?result",
        "datum van uitgave" : "{?identity dbpedia-owl:releaseDate ?result} UNION {?identity prop-nl:releasedatum ?result}",
        "uitgave datum" 	: "{?identity dbpedia-owl:releaseDate ?result} UNION {?identity prop-nl:releasedatum ?result}"	,
        "uitgavedaum" 		: "{?identity dbpedia-owl:releaseDate ?result} UNION {?identity prop-nl:releasedatum ?result}"	,
        "schrijver" 		: "?identity dbpedia-owl:writer ?name. ?name rdfs:label ?result",
        "schrijvers" 		: "?identity dbpedia-owl:writer ?name. ?name rdfs:label ?result",
        "complete naam"		: "?identity dbpedia-owl:longName ?result",
        "geboortenaam" 		: "?identity dbpedia-owl:longName ?result",
        "site"				: "?identity prop-nl:website ?result",
        "URL"				: "?identity prop-nl:website ?result",
        "url"				: "?identity prop-nl:website ?result",
        "label"				: "?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
        "platenmaatschappij": "?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
        "platenmaatschappijen": "?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
        "uitgever"			: "?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
        "herkomst" 			: "?identity dbpedia-owl:origin ?place. ?place rdfs:label ?result",
        "muziekstijl"		: "?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
        "genre"				: "?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
        "genres"			: "?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
        "stijl"				: "?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
        "muzieksoort"		: "?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
        "abstract"	 		: "?identity dbpedia-owl:abstract ?result",
        "platen"			: "?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
        "plaat"				: "?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
        "albums"			: "?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
        "album"				: "?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
        "beginjaar": "?identity prop-nl:jarenActief ?result",
        "geloof": "?identity prop-nl:geloof ?result",
        "naam": "?identity prop-nl:volledigeNaam ?result",
        "schreef": "?identity dbpedia-owl:musicalArtist ?result",
        "geschreven": "?identity dbpedia-owl:musicalArtist ?result",
        "auteur": "?identity dbpedia-owl:musicalArtist ?result",
        "componist": "?identity dbpedia-owl:musicalArtist ?result",
        "credits": "?identity dbpedia-owl:musicalArtist ?result",
        "speelde": "?identity dbpedia-owl:bandMember ?bandMember . ?bandMember prop-nl:naam ?result",
        'bandlid': "?identity dbpedia-owl:bandMember ?bandMember . ?bandMember prop-nl:naam ?result",
        'lid': "?identity dbpedia-owl:bandMember ?bandMember . ?bandMember prop-nl:naam ?result",
    }

    relation = None
    try:
        relation = relations[Property]
    except KeyError:
        # TODO: Verkrijg relatie uit similarwords
        pass

    if not relation:
        raise NoPropertyRelationException
    return relation


def construct_query(wikiPageID, relation):
    baseQuery = """
                PREFIX prop-nl:     <http://nl.dbpedia.org/property/>
                PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
                PREFIX dbres: <http://dbpedia.org/resource/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX dc: <http://purl.org/dc/elements/1.1/>

                SELECT STR(?result)
                WHERE  {{
                    ?identity dbpedia-owl:wikiPageID {} .
                    {}
                }}
                """
    return baseQuery.format(wikiPageID, relation)


def query(source, query):
    """
    Voert een meegegeven SPARQL-query uit op het gekozen SPARQL endpoint.

    :param source: het te gebruiken SPARQL endpoint als string.
    :param query: de uit te voeren query als string.
    :return: het resultaat als JSON.
    """
    try:
        sparql = SPARQLWrapper(source)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        result = sparql.query().convert()
        return result
    except:
        return None


def output(result):
    """
    Geeft het antwoord terug op de gestelde vraag aan de gebruiker.

    :param result: het resultaat als JSON
    :return: geen (het antwoord is teruggegeven) of NoResultException (geen resultaten gevonden)
    """
    results = result["results"]["bindings"]
    if len(results) == 0:
        raise NoResultException
    else:
        for item in results:
            for argument in item:
                answer = item[argument]["value"]
                try:
                    parsableDate = answer.split("+")[0]
                    localDate = datetime.strptime(parsableDate, "%Y-%m-%d")
                    print(localDate.strftime("%d-%m-%Y"))
                except ValueError:
                    print(answer)


# Helper functions
def load_anchors(file):
    with open(file, 'r') as f:
        reader = csv.reader(f)
        anchor = list(reader)
    return anchor

# Self-defined exceptions
class NoConceptException(Exception):
    # In case the concept couldn't be found
    pass


class NoConceptIDException(Exception):
    # In case the Wikipedia ID of the concept couldn't be found
    pass


class NoPropertyException(Exception):
    # In case the property couldn't be found
    pass


class NoPropertyRelationException(Exception):
    # In case there is no relation found for the property
    pass


class NoResultException(Exception):
    pass


if __name__ == "__main__":
    anchors = load_anchors("../anchor_summary.csv")

    # Check for command-line argument
    if len(sys.argv) >= 2:
        with open(sys.argv[1], 'r') as questions:
            for question in questions:
                main(question, anchors)

    # Check standard input
    elif not sys.stdin.isatty():
        for line in sys.stdin:
            main(line, anchors)

    # Resort to user input (or if the user chooses so: test questions)
    else:
        user_prompt = "Stel uw vraag (enter voor voorbeeldvragen; 'stop' om te stoppen): "

        user_question = input(user_prompt)
        while user_question != "stop":

            # If no input, run the test questions
            if len(user_question) == 0:
                main("Wat is de volledige naam van Anouk?", anchors)
                main("Wat is de geboortedatum van Dries Roelvink?", anchors)
                main("Wie zijn de leden van Muse?", anchors)
                main("Wie zijn de voormalige leden van BZN?", anchors)
                main("Wat is de website van Rihanna?", anchors)
                main("Wat is het genre van Lady Gaga?", anchors)
                main("Wat is het beroep van Anouk?", anchors)
                main("Wat zijn de platenmaatschappijen van de Kaiser Chiefs?", anchors)
                main("Wat is de bezetting van The Wombats?", anchors)
                main("Wat is de oorsprong van de Arctic Monkeys?", anchors)

                # Toegevoerd type 1: Geef de X van Y
                main("Geef de website van The Wombats.", anchors)
                main("Geef de volledige naam van Anouk.", anchors)

                # Toegevoegd type 2: Welke X (...) Y?
                main("Welke genres bedient Lady Gaga?", anchors)
                main("Welke leden heeft Muse?", anchors)

                # Toegevoegd type 3: Wanneer is Y X?
                main("Wanneer is Dries Roelvink geboren?", anchors)
                main("Wanneer is Anouk geboren?", anchors)

                # Toegevoegd type 4: Hoe is/zijn Y X?
                main("Hoe zijn The Wombats samengesteld?", anchors)
                main("Hoe zijn de Kaiser Chiefs samengesteld?", anchors)

            # Else, find the answer for the asked question
            else:
                main(user_question, anchors)

            # After the question has been handled, ask again.
            user_question = input(user_prompt)