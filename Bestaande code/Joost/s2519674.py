#s2519674

import csv
import socket
import sys
from lxml import etree
from SPARQLWrapper import SPARQLWrapper, JSON

class NoPropertyException(Exception):
    pass

class NoResultException(Exception):
    pass

# parse input sentence and return alpino output as an xml element tree
def alpino_parse(sent, host="zardoz.service.rug.nl", port=42424):
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.connect((host,port))
	sent = sent + "\n\n"
	sentbytes= sent.encode("utf-8")
	s.sendall(sentbytes)
	bytes_received= b''
	while True:
		byte = s.recv(8192)
		if not byte:
			break
		bytes_received += byte
	xml = etree.fromstring(bytes_received)

	# retreive identity
	identity = []
	names = xml.xpath("//node[@rel='obj1' and @ntype='eigen'] | //node[@spectype='deeleigen']")
	for name in names:
		x = name.attrib["word"]
		identity.append(x)
	identity = " ".join(identity)

	# retreive relation type
	relation = []
	names = xml.xpath("//node[@pos='adj' and @rel='mod'] | //node[@rel='hd' and @pos='noun']")
	for name in names:
		x = name.attrib["word"]
		relation.append(x)
	relation = " ".join(relation)

	return relation, identity

def getQuestion():
	print("\nStel hier uw vraag:")
	question = input(">> ")
	return question

def wikidump():
	with open('anchor_summary.csv', 'r') as f:
	    reader = csv.reader(f)
	    anchor = list(reader)

	return anchor

def helpQuestions():
	print("\nDit zijn de voorbeeldvragen:\n")
	print("Wie zijn de leden van Coldplay?")
	print("Wat is de geboortedatum van Chris Martin?")
	print("Wat is de overlijdensdatum van Louis Armstrong?")
	print("Wie is de schrijver van The Scientist?")
	print("Wat is de volledige naam van Guy Berryman?")
	print("Wat is de uitgave datum van The Scientist?")
	print("Wat is de website van 30 Seconds To Mars?")
	print("Wat zijn de platenmaatschappijen van U2?")
	print("Waar ligt de oorsprong van Architects?")
	print("Wat is de bijnaam van Paul David Hewson?")
	print("Wat zijn de genres van Linkin Park?")
	print("Wat is de abstract van Linkin Park?")
	print("Wat zijn de albums van Linkin Park?")

def getID(entity, anchor):
	result = False
	for row in anchor:
		if row[0].lower() == entity.lower():
			result = row[1]
	if not result:
		raise NoPropertyException
	propID = (result.split(":"))[0]
	return propID

def generateQuery(relation, identity, anchor):
	basis_query = """
        SELECT STR(?result) as ?result
        WHERE  {{ ?identity dbpedia-owl:wikiPageID 
            {}
        }}ORDER BY ?result
        """

	queryDict = {
				"leden" 			: " . {{?identity dbpedia-owl:bandMember ?member.} UNION {?identity dbpedia-owl:formerBandMember ?member .} .} UNION {?identity dbpedia-owl:musicBand ?member.} . ?member rdfs:label ?result",	
				"geboortedatum" 	: " . ?identity dbpedia-owl:birthDate ?result",
				"verjaardag" 		: " . ?identity dbpedia-owl:birthDate ?result",
				"overlijdensdatum" 	: " . ?identity dbpedia-owl:deathDate ?result",
				"bijnaam" 			: " . ?identity prop-nl:bijnaam ?result",
				"datum van uitgave" : " . {?identity dbpedia-owl:releaseDate ?result} UNION {?identity prop-nl:releasedatum ?result}",
				"uitgave datum" 	: " . {?identity dbpedia-owl:releaseDate ?result} UNION {?identity prop-nl:releasedatum ?result}"	,
				"uitgavedaum" 		: " . {?identity dbpedia-owl:releaseDate ?result} UNION {?identity prop-nl:releasedatum ?result}"	,
				"schrijver" 		: " . ?identity dbpedia-owl:writer ?name. ?name rdfs:label ?result",
				"schrijvers" 		: " . ?identity dbpedia-owl:writer ?name. ?name rdfs:label ?result",
				"volledige naam" 	: " . ?identity dbpedia-owl:longName ?result",	
				"complete naam"		: " . ?identity dbpedia-owl:longName ?result",	
				"geboortenaam" 		: " . ?identity dbpedia-owl:longName ?result",	
				"site"				: " . ?identity prop-nl:website ?result",
				"website"			: " . ?identity prop-nl:website ?result",
				"URL"				: " . ?identity prop-nl:website ?result",
				"url"				: " . ?identity prop-nl:website ?result",
				"label"				: " . ?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
				"platenmaatschappij": " . ?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
				"platenmaatschappijen": " . ?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
				"uitgever"			: " . ?identity prop-nl:recordLabel ?label. ?label rdfs:label ?result",
				"oorsprong" 		: " . ?identity dbpedia-owl:origin ?place. ?place rdfs:label ?result",
				"herkomst" 			: " . ?identity dbpedia-owl:origin ?place. ?place rdfs:label ?result",
				"muziekstijl"		: " . ?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
				"genre"				: " . ?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
				"genres"			: " . ?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
				"stijl"				: " . ?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
				"muzieksoort"		: " . ?identity dbpedia-owl:genre ?label. ?label rdfs:label ?result",
				"abstract"	 		: " . ?identity dbpedia-owl:abstract ?result",
				"platen"			: " . ?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
				"plaat"				: " . ?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
				"albums"			: " . ?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result",
				"album"				: " . ?album dbpedia-owl:identity ?identity. ?album rdfs:label ?result"
				}

	the_where = False

	the_where = getID(identity, anchor) + queryDict[relation]

	query = basis_query.format(the_where)
	return query

def runQuestion(question, anchor):
	relation, identity = alpino_parse(question)
	query = generateQuery(relation, identity, anchor)
	sparql = SPARQLWrapper("http://nl.dbpedia.org/sparql")
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	count = 0
	for result in results["results"]["bindings"]:
		count += 1
	if count == 0:
		raise NoResultException
	for result in results["results"]["bindings"]:
		for arg in result :
			answer = result[arg]["value"]
			print(answer)

def main():
	# reading anchor_summary.csv
	try:
		anchor = wikidump()
	except FileNotFoundError:
		print("\nHet bestand anchor_summary.csv is niet aanwezig.")
		print("Het programma gaat nu afsluiten.\n")
		exit()
	except NameError:
		print("\nDe CSV-package is niet aanwezig op deze computer.\n")
		exit()

	print("Typ een vraag om een antwoord te krijgen,\n\"stop\" om te stoppen,\nof niets (\"Enter\") om voorbeelden te zien.")
	while True:

		try:
			question = ""
			while (True):
				question = getQuestion()
				if question == "":
					helpQuestions()
				elif question.lower() == "stop":
					exit()
				else:
					runQuestion(question, anchor)
		# only if property not in anchor_summary
		except NoPropertyException:
			print("Er kon niets gevonden worden over dit onderwerp.")
		#only if no results in JSON
		except NoResultException:
			print("Er konden geen antwoorden gevonden worden op de vraag.")
		# only if no connection to server
		except socket.gaierror:
			print("Er kon geen verbinden gemaakt worden met de (alpino)server.")
			print("Het programma gaat nu afsluiten.\n")
			exit()
		# only if relation not present
		except KeyError:
			print("De gevraagde relatie kan niet beantwoord worden.")
		except NameError:
			print("\nDe benodigde packages zijn niet aanwezig op deze computer.\n")
			exit()

if __name__ == "__main__":
    main()