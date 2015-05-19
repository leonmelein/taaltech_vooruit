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
    while question[-1] == "\n" or question[-1] == " ":
        question = question[:-1]
    theList = [question]
    try:
        Concept, Property = analyze_question(parse)

        # Find relevant information for query
        # # Concept
        wikiID = find_resource(Concept, anchors)

        # # Property
        relation = find_relation(Property)

        # Retrieve answer
        answer = query(source_DBPedia, construct_query(wikiID, relation))
        answerList = output(answer)
        theList = theList + answerList
        return theList
    except NoConceptException:
        # TODO: Meaningful error handling
        print("No Concept")
        theList = theList + ["No Concept"]
        return theList
    except NoPropertyException:
        # TODO: Meaningful error handling
        print("No Property")
        theList = theList + ["No Property"]
        return theList
    except NoConceptIDException:
        # TODO: Meaningful error handling
        print("No wikiPageID")
        theList = theList + ["No wikiPageID"]
        return theList
    except NoPropertyRelationException:
        # TODO: Meaningful error handling
        print("No relation")
        theList = theList + ["No relation"]
        return theList
    except NoResultException:
        # TODO: Meaningful error handling
        print("No results")
        theList = theList + ["No results"]
        return theList

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
    vraagwoorden = xml.xpath('//node[@rel="whd" and (@root="wanneer" or @root="waar")]')
    for prop in properties:
        relation.append(prop.attrib["word"])
    for vraagwoord in vraagwoorden:
        word = (vraagwoord.attrib["word"]).lower()
        if word == "wanneer" or word == "waar":
            relation = [word] + relation
    Property = " ".join(relation)

    # Check if we've found a property
    if len(Property) == 0:
        raise NoPropertyException
    else:
        print("property: " + Property)

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

def find_relation(Property):
    """
    Probeert de passende relatie bij een bepaalde eigenschap te vinden. Gebruikt hiervoor zowel een basisset
    eigenschappen als een bestand met synoniemen, op basis waarvan eigenschappen kunnen worden verkregen.

    :param propert: de eigenschap als string.
    :return: de geschikte relatie als
    """
    relations = {
        "geboortedatum"     : "?identity dbpedia-owl:birthDate ?result",
        "naam"              : "?identity dbpedia-owl:longName ?result",
        "leden"             : "?identity dbpedia-owl:bandMember ?bandMember . ?bandMember rdfs:label ?result",
        "genre"             : "?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
        "oorsprong"         : "?identity dbpedia-owl:origin ?place. ?place rdfs:label ?result",
        "voormalige leden"  : "?identity dbpedia-owl:formerBandMember ?bandMember . ?bandMember prop-nl:naam ?result",
        "bezetting"         : "?identity prop-nl:functie ?bandMember . ?bandMember rdfs:label ?result",
        "overlijdensdatum"  : "?identity dbpedia-owl:deathDate ?result",
        "bijnaam"           : "?identity prop-nl:bijnaam ?result",
        "uitgavedaum"       : "{?identity dbpedia-owl:releaseDate ?result} UNION {?identity prop-nl:releasedatum ?result}",
        "schrijvers"        : "?identity dbpedia-owl:writer ?name. ?name rdfs:label ?result",
        "website"           : "?identity prop-nl:website ?result",
        "label"             : "?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
        "abstract"          : "?identity dbpedia-owl:abstract ?result",
        "albums"            : "?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
        "beginjaar"         : "?identity prop-nl:jarenActief ?result",
        "geloof"            : "?identity prop-nl:geloof ?result",
        "schreef"           : "?identity dbpedia-owl:musicalArtist ?result",
        "waar geboren"      : "?identity dbpedia-owl:birthPlace ?place. ?place rdfs:label ?result"
    }

    subrelations = {
        "geboortedatum"     : "geboortedatum",
        "wanneer geboren"   : "geboortedatum",
        "verjaardag"        : "geboortedatum",
        "datum geboren"     : "geboortedatum",
        "waar geboren"      : "waar geboren",
        "geboorteplaats"    : "waar geboren",
        "land geboren"      : "waar geboren",
        "stad geboren"      : "waar geboren",
        "dorpje geboren"    : "waar geboren",
        "plaats geboren"    : "waar geboren",
        "Nederlandse plaats geboren":"waar geboren",
        "volledige naam"    : "naam",
        "complete naam"     : "naam",
        "geboortenaam"      : "naam",
        "gehele naam"       : "naam",
        "artiest volledige naam": "naam",
        "naam"              : "naam",
        "echte naam"        : "naam",
        "leden"             : "leden",
        "bandleden"         : "leden",
        "leden band"        : "leden",
        "speelde"           : "leden",
        "namen leden"       : "leden",
        "bandlid"           : "leden",
        "huidige bandleden" : "leden",
        "lid"               : "leden",
        "personen band"     : "leden",
        "muziekstijl"       : "genre",
        "genre"             : "genre",
        "genres"            : "genre",
        "genre muziek"      : "genre",
        "genres muziek"     : "genre",
        "genres gerekend"   : "genre",
        "stijl muziek"      : "genre",
        "genre artiest(en)" : "genre",
        "genres nummers"    : "genre",
        "genre nummers"     : "genre",
        "genre(s) nummers"  : "genre",
        "genre(s) muziek"   : "genre",
        "stijl"             : "genre",
        "muzieksoort"       : "genre",
        "soort"             : "genre",
        "herkomst"          : "oorsprong",
        "waar herkomst"     : "oorsprong",
        "oorsprong"         : "oorsprong",
        "stad band"         : "oorsprong",
        "waar band"         : "oorsprong",
        "waar origineel"    : "oorsprong",
        "waar opgericht"    : "oorsprong",
        "waar"              : "oorsprong",
        "land oorsprong"    : "oorsprong",
        "waar oorsprong"    : "oorsprong",
        "stad opgericht"    : "oorsprong",
        "voormalige leden"  : "voormalige leden",
        "voormalige lid"    : "voormalige leden",
        "ex-leden"          : "voormalige leden",
        "ex-leden rockband" : "voormalige leden",
        "bezetting"         : "bezetting",
        "functie"           : "bezetting",
        "functies"          : "bezetting",
        "samengesteld"      : "bezetting",
        "overlijdensdatum"  : "overlijdensdatum",
        "wanneer overleden" : "overlijdensdatum",
        "dag overleden"     : "overlijdensdatum",
        "jaar overleden"    : "overlijdensdatum",
        "bijnaam"           : "bijnaam",
        "bijnamen"          : "bijnaam",
        "wel genoemd"       : "bijnaam",
        "datum van uitgave" : "uitgavedatum",
        "uitgave datum"     : "uitgavedatum"  ,
        "uitgavedaum"       : "uitgavedatum"  ,
        "schrijver"         : "schrijvers",
        "schrijvers"        : "schrijvers",
        "site"              : "website",
        "URL"               : "website",
        "url"               : "website",
        "website"           : "website",
        "officiële website" : "website",
        "officiële website band" : "website",
        "officiele website" : "website",
        "website vinden informatie":"website",
        "label"             : "label",
        "recordlabel"       : "label",
        "recordlabels"      : "label",
        "muzieklabel"       : "label",
        "muzieklabel DJ"    : "label",
        "labels"            : "label",
        "uitgever"          : "label",
        "uitgevers"         : "label",
        "publisher"         : "label",
        "platenmaatschappij": "label",
        "platenmaatschappijen": "label",
        "platenmaatschappijen contract" : "label",
        "platenmaatschappijen gepubliceerd" : "label",
        "labels muziek uitgebracht" : "label",
        "abstract"          : "abstract",
        "platen"            : "albums",
        "plaat"             : "albums",
        "albums"            : "albums",
        "album"             : "albums",
        "albums uitgebracht": "albums",
        "albums uitgegeven" : "albums",
        "albums gemaakt"    : "albums",
        "beginjaar"         : "beginjaar",
        "wanneer begonnen"  : "beginjaar",
        "begin datum"       : "beginjaar",
        "wanneer opgericht" : "beginjaar",
        "begindatum"        : "beginjaar",
        "jaar band opgericht": "beginjaar",
        "jaar opgericht"    : "beginjaar",
        "wanneer band opgericht" : "beginjaar",
        "wanneer opgericht" : "beginjaar",
        "geloof"            : "geloof",
        "schreef"           : "schreef",
        "geschreven"        : "schreef",
        "auteur"            : "schreef",
        "componist"         : "schreef",
        "liedje geschreven" : "schreef",
        "credits"           : "schreef"
    }

    relation = None
    try:
        relation = relations[subrelations[Property]]
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

                SELECT DISTINCT STR(?result)
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

def resolveRDFS(answer):
    query = """
    PREFIX prop-nl: <http://nl.dbpedia.org/property/>
    PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT DISTINCT STR(?answerstr)
    WHERE {
    <"""+answer+"""> rdfs:label ?answerstr
    } 
    """
    sparql = SPARQLWrapper('http://nl.dbpedia.org/sparql')
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for result in results["results"]["bindings"]:
        for arg in result :
            answer = result[arg]["value"]
    return answer

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
        answerList = []
        for item in results:
            for argument in item:
                answer = item[argument]["value"]
                if answer[0:17] == "http://nl.dbpedia":
                    answer = resolveRDFS(answer)
                try:
                    parsableDate = answer.split("+")[0]
                    localDate = datetime.strptime(parsableDate, "%Y-%m-%d")
                    print(localDate.strftime("%d-%m-%Y"))
                    answerList.append(localDate.strftime("%d-%m-%Y"))
                except ValueError:
                    print(answer)
                    answerList.append(answer)
        return answerList

def countList(completeList):
    NoRelation = 0
    NoConcept = 0
    NoWikipageID = 0
    NoProperty = 0
    NoResult = 0
    for question in completeList:
        if question[2] == "No results":
            NoResult += 1
        elif question[2] == "No Property":
            NoProperty += 1
        elif question[2] == "No Concept":
            NoConcept += 1
        elif question[2] == "No relation":
            NoRelation += 1
        elif question[2] == "No wikiPageID":
            NoWikipageID += 1
    notAnswered = NoRelation + NoConcept + NoWikipageID + NoProperty + NoResult
    total = len(completeList)
    print("Total: " + str(total) + ". And " + str(total-notAnswered) + " answered.")
    print("No relation: " + str(NoRelation))
    print("No concept: " + str(NoConcept))
    print("No wikiID: " + str(NoWikipageID))
    print("No property: " + str(NoProperty))
    print("No result: " + str(NoResult))

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
        completeList = []
        count = 1
        with open(sys.argv[1], 'r') as questions:
            for question in questions:
                print(question)
                theList = main(question, anchors)
                theList = [count] + theList
                completeList.append(theList)
                count += 1
        print(completeList)
        countList(completeList)

    # Check standard input
    elif not sys.stdin.isatty():
        for line in sys.stdin:
            main(line, anchors)

    # Resort to user input (or if the user chooses so: test questions)
    else:
        user_prompt = "Stel uw vraag (enter voor voorbeeldvragen; 'stop' om te stoppen)."
        print(user_prompt)
        user_question = input(">> ")
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
            print("\n" + user_prompt)
            user_question = input(">> ")