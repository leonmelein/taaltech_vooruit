# Taaltechnologie - Week 4
# Léon Melein - S2580861
#!/usr/bin/env python3
import socket
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
from lxml import etree
from datetime import datetime
import csv


def main(question):
    """
    Analyseert een gestelde muziekvraag en probeert deze met behulp van DBPedia te beantwoorden.

    :param question: De door de gebruiker vraag als string.
    """
    properties = {
        "geboortedatum": "?artist dbpedia-owl:birthDate ?result",
        "volledige naam": "?artist prop-nl:volledigeNaam ?result",
        "leden": "?artist dbpedia-owl:bandMember ?bandMember . \n ?bandMember prop-nl:naam ?result",
        "voormalige leden": "?artist dbpedia-owl:formerBandMember ?bandMember . \n ?bandMember prop-nl:naam ?result",
        "website": "?artist prop-nl:website ?result",
        "genre": "?artist prop-nl:genre ?genre . \n ?genre rdfs:label ?result",
        "genres": "?artist prop-nl:genre ?genre . \n ?genre rdfs:label ?result",
        "beroep": "?artist prop-nl:beroep ?result",
        "platenmaatschappijen": "?artist dbpedia-owl:parentOrganisation ?label . \n  ?label rdfs:label ?result",
        "bezetting": "?artist prop-nl:functie ?bandMember . \n ?bandMember rdfs:label ?result",
        "oorsprong": "?artist dbpedia-owl:origin ?origin . \n ?origin dbpedia-owl:name ?result",
        "geboren": "?artist dbpedia-owl:birthDate ?result",
        "samengesteld": "?artist prop-nl:functie ?bandMember . \n ?bandMember rdfs:label ?result",
    }

    source_DBPedia = "http://nl.dbpedia.org/sparql"
    baseQuery = """
                PREFIX prop-nl:     <http://nl.dbpedia.org/property/>
                PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
                PREFIX dbres: <http://dbpedia.org/resource/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX dc: <http://purl.org/dc/elements/1.1/>

                SELECT ?result
                WHERE  {{
                    {}
                }}
                """
    if len(question.split(' ')) > 2:

        concept, prop = analyzeAlpino(question)
        try:
            # Analyze concept
            searchResult = csvSearch("../../anchor_summary.csv", concept)

            if searchResult is not None:

                # Get all possible references for the concept
                possiblePages = (searchResult.strip('"')).split(";")

                # Get the ID of the most frequently referenced page
                pageID = (possiblePages[0].split(":"))[0]

                # Analyze property
                queryProp = properties[prop]

                # Construct query
                whereClause = "?artist dbpedia-owl:wikiPageID " + pageID + " .\n" + queryProp
                query = baseQuery.format(whereClause)

                # Find answer
                queryResult = retrieve(source_DBPedia, query)
                if queryResult is not None:
                    output(question, query, queryResult)
                else:
                    print("Deze vraag kan helaas niet beantwoord worden. <Geen queryresultaat>")
            else:
                print("Deze vraag kan helaas niet beantwoord worden. <Concept niet gevonden>")

        except KeyError:
            print("Deze vraag kan helaas niet beantwoord worden. <Eigenschap niet gevonden>")
    else:
        print("Deze vraag kan helaas niet beantwoord worden. <Vraag niet juist gevormd>")


def analyzeAlpino(question, host='zardoz.service.rug.nl', port=42424):
    """
    Analyseert de gestelde vraag tot op het niveau van het concept en de eigenschap in natuurlijke taal, met hulp van
    Alpino voor het parsen van de vraag.

    :param question: De door de gebruiker gestelde vraag als string.
    :return: concept en eigenschap in natuurlijke taal als strings in een tuple.
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

    # Get concept
    theConcept = ""
    theProperty = ""
    concept = xml.xpath(
        '//node[@rel="obj1" and @ntype="eigen"] | //node[@spectype="deeleigen"] | //node[@rel="su" and @ntype="eigen"]')
    if len(concept) > 0:
        for part in concept:
            theConcept += part.attrib["word"] + " "

    # Get property
    property = xml.xpath(
        '//node[@pos="adj" and @rel="mod"] | //node[@rel="hd" and @pos="noun"] | //node[@rel="vc"]/node[@rel="hd"]')
    if len(property) > 0:
        for part in property:
            theProperty += part.attrib["word"] + " "

    return theConcept.strip(), theProperty.strip()


def analyzeManual(question):
    """
    Analyseert de gestelde vraag tot op het niveau van het concept en de eigenschap in natuurlijke taal.

    :param question: De door de gebruiker gestelde vraag als string.
    :return: concept en eigenschap in natuurlijke taal als strings in een tuple.
    """
    concept = ""
    prop = ""

    # Analyze question
    questionParts = question.split(" ")
    omitWH = questionParts[3:]

    # # Property
    foundFullProperty = False
    i = 0
    while not foundFullProperty and i in range(0, len(omitWH)):
        if omitWH[i] != 'van':
            if prop == "":
                prop = omitWH[i]
            else:
                prop = prop + " " + omitWH[i]
            i += 1
        else:
            foundFullProperty = True

    # # Concept
    foundFullConcept = False
    i = -1
    while not foundFullConcept:
        if omitWH[i] not in ['de', 'het', 'een', 'van', 'band']:
            if concept == "":
                concept = omitWH[i]
            else:
                concept = omitWH[i] + " " + concept
            i -= 1
        else:
            foundFullConcept = True

    concept = concept.replace("?", "")
    concept = concept.replace("\n", "")
    return concept, prop


def csvSearch(file, term):
    """
    Zoekt in anchor_summary.csv naar een pagina die matcht met het eerder gevonden concept.

    :param file: de naam van het bestand met anchor texts als string.
    :param term: de zoekterm als string
    :return: het zoekresultaat als string óf None als er geen resultaat is gevonden
    """
    result = None

    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row[0] == '"{}"'.format(term):
                result = row[1]
                return result
    return result


def retrieve(source, query):
    """
    Voert een meegegeven SPARQL-query uit op het gekozen SPARQL endpoint.

    :param source: de te gebruiken DBPedia endpoint als string.
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


def output(question, query, result):
    """
    Print de vraag, de query en de uitkomsten van de query op het scherm.

    :param question: de vraag als string.
    :param query: de query als string.
    :param result: het resultaat als JSON.
    """
    print("Vraag: {}\nQuery: {}\nAntwoord:".format(question, query))
    for item in result["results"]["bindings"]:
        for argument in item:
            answer = item[argument]["value"]
            try:
                parsableDate = answer.split("+")[0]
                localDate = datetime.strptime(parsableDate, "%Y-%m-%d")
                print(localDate.strftime("%d-%m-%Y"))
            except ValueError:
                print(answer)
    print("\n")


if __name__ == "__main__":

    # Check for command-line argument
    if len(sys.argv) >= 2:
        with open(sys.argv[1], 'r') as questions:
            for question in questions:
                print(question)
                main(question)

    # Check standard input
    elif not sys.stdin.isatty():
        for line in sys.stdin:
            main(line)

    # Resort to user input (or if the user chooses so: test questions)
    else:
        user_prompt = "Stel uw vraag (enter voor voorbeeldvragen; 'stop' om te stoppen): "

        user_question = input(user_prompt)
        while user_question != "stop":

            # If no input, run the test questions
            if len(user_question) == 0:
                main("Wat is de volledige naam van Anouk?")
                main("Wat is de geboortedatum van Dries Roelvink?")
                main("Wie zijn de leden van Muse?")
                main("Wie zijn de voormalige leden van BZN?")
                main("Wat is de website van Rihanna?")
                main("Wat is het genre van Lady Gaga?")
                main("Wat is het beroep van Anouk?")
                main("Wat zijn de platenmaatschappijen van de Kaiser Chiefs?")
                main("Wat is de bezetting van The Wombats?")
                main("Wat is de oorsprong van de Arctic Monkeys?")

                # Toegevoerd type 1: Geef de X van Y
                main("Geef de website van The Wombats.")
                main("Geef de volledige naam van Anouk.")

                # Toegevoegd type 2: Welke X (...) Y?
                main("Welke genres bedient Lady Gaga?")
                main("Welke leden heeft Muse?")

                # Toegevoegd type 3: Wanneer is Y X?
                main("Wanneer is Dries Roelvink geboren?")
                main("Wanneer is Anouk geboren?")

                # Toegevoegd type 4: Hoe is/zijn Y X?
                main("Hoe zijn The Wombats samengesteld?")
                main("Hoe zijn de Kaiser Chiefs samengesteld?")

            # Else, find the answer for the asked question
            else:
                main(user_question)

            # After the question has been handled, ask again.
            user_question = input(user_prompt)