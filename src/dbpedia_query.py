# functions to create the proper query and proper output for the questions

from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime
from exception_classes import *

def construct_query(wikiPageID, relation, selection="STR(?result)"):
    baseQuery = """
                PREFIX prop-nl:     <http://nl.dbpedia.org/property/>
                PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
                PREFIX dbres: <http://dbpedia.org/resource/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                PREFIX dc: <http://purl.org/dc/elements/1.1/>

                SELECT DISTINCT {}
                WHERE  {{
                    {} .
                    {}
                }}
                """
    if wikiPageID[0] == "?":
        wikiPageID = "?identity rdfs:label '" + wikiPageID[1:] + "'@nl"
    else:
        wikiPageID = "?identity dbpedia-owl:wikiPageID " + wikiPageID
    return baseQuery.format(selection, wikiPageID, relation)


def query(query):
    """
    Voert een meegegeven SPARQL-query uit op het gekozen SPARQL endpoint.

    :param query: de uit te voeren query als string.
    :return: het resultaat als JSON.
    """
    try:
        sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        result = sparql.query().convert()
        return result
    except:
        return None

def resolveRDFS(answer):
    """
    Voert een SPARQL-query uit om ipv resource-url een (label)string te krijgen.

    :param answer: de resource-url.
    :return: het antwoord, er is hier ook maar 1 antwoord mogelijk.
    """
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