#!/usr/bin/env python3
# 10-05-2015 - S2497867 - Reinard van Dalen
import socket
from lxml import etree
from SPARQLWrapper import SPARQLWrapper, JSON
import csv
import re
import sys

def alpino_parse(sent, host='zardoz.service.rug.nl', port=42424):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((host,port))
    sent = sent + "\n\n"
    sentbytes= sent.encode('utf-8')
    s.sendall(sentbytes)
    bytes_received= b''
    while True:
        byte = s.recv(8192)
        if not byte:
            break
        bytes_received += byte
    xml = etree.fromstring(bytes_received)
    return xml

def analyzeSentence(sentence):
	xml = alpino_parse(sentence)
	Xvalue = ""
	Yvalue = ""
	# Vraagsoort 1: Wat/Wie is/zijn X van Y?
	try:
		names = xml.xpath('//node[../@rel="su" and @rel="hd" and ..//@rel="mod"]')
		for name in names:
			Xvalue = Xvalue + name.attrib["word"] + " "
	except:
		donothing = ""
	try:
		names = xml.xpath('//node[@rel="obj1" and @ntype="eigen"]')
		for name in names:
			Yvalue = Yvalue + name.attrib["word"] + " "
	except:
		donothing = ""
	try:
		names = xml.xpath('//node[@spectype="deeleigen"]')
		for name in names:
			Yvalue = Yvalue + name.attrib["word"] + " "
	except:
		donothing = ""
	try:
		names = xml.xpath('//node[../@rel="obj1" and @ntype="eigen"]')
		for name in names:
			Yvalue = Yvalue + name.attrib["word"] + " "
	except:
		donothing = ""

	if Xvalue and Yvalue != "":
		return(Xvalue.strip(),Yvalue.strip())

	# Vraagsoort 2: Wie X er gitaar bij Y?
	try:
		names = xml.xpath('//node[@rel="hd" and ../@rel="body" and ..//node[@rel="mod" and ../@rel="body"]]')
		for name in names:
			Xvalue = Xvalue + name.attrib["word"] + " "
	except:
		donothing = ""

	if Xvalue and Yvalue != "":
		return(Xvalue.strip(),Yvalue.strip())

	# Vraagsoort 3: Wie X het nummer Y?
	try:
		names = xml.xpath('//node[@rel="hd" and @pt="ww" and ..//node[@rel="app" and ../@rel="obj1" and ../../@rel="body"]]')
		for name in names:
			Xvalue = Xvalue + name.attrib["word"] + " "
	except:
		donothing = ""

	if Xvalue and Yvalue != "":
		return(Xvalue.strip(),Yvalue.strip())

	# Vraagsoort 4: Geef X van Y
	try:
		names = xml.xpath('//node[@rel="hd" and @pt="n" and ../@rel="obj1" and ..//node[@rel="mod"]]')
		for name in names:
			Xvalue = Xvalue + name.attrib["word"] + " "
	except:
		donothing = ""

	if Xvalue and Yvalue != "":
		return(Xvalue.strip(),Yvalue.strip())

	# Vraagsoort 5: Wie heeft het nummer Y X?
	try:
		names = xml.xpath('//node[@rel="hd" and ../@rel="vc" and ..//node[@rel="obj1"]]')
		for name in names:
			Xvalue = Xvalue + name.attrib["word"] + " "
	except:
		donothing = ""

	if Xvalue and Yvalue != "":
		return(Xvalue.strip(),Yvalue.strip())

	# Vraagsoort 6: Welk persoon was X van Y?
	try:
		names = xml.xpath('//node[@rel="hd" and ../@rel="predc" and ..//node[@rel="obj1" and ../@rel="mod" and ../../@rel="predc"]]')
		for name in names:
			Xvalue = Xvalue + name.attrib["word"] + " "
	except:
		donothing = ""

	if Xvalue and Yvalue != "":
		return(Xvalue.strip(),Yvalue.strip())

	# Als er niks is gevonden door Alpino
	if Xvalue == "":
		Xvalue = "Geen Xvalue gevonden"
	if Yvalue == "":
		Yvalue = "Geen Yvalue gevonden"
	return(Xvalue.strip(),Yvalue.strip())

def createDict(anchor,pagefile):
	anchorDict = {}
	with open(anchor, 'r') as f:
		reader = csv.reader(f)
		for row in reader:
			if len(row) >= 2:
				pages = ''.join(row[1]).split(';')
				count = 0
				bestpage = ""
				for page in pages:
					index = page.split(':')
					if len(index) == 2:
						try:
							index[1] = int(index[1])
						except:
							break
						if index[1] >= count:
							count = index[1]
							bestpage = index[0]
				anchorDict[row[0]] = bestpage
	f.close()
	print("...")
	pageDict = {}
	with open(pagefile, 'r') as f:
		reader = csv.reader(f)
		for row in reader:
			if len(row) >= 2:
				pageDict[row[0]] = "http://nl.dbpedia.org/resource/"+re.sub('[ ]','_',row[1])
	f.close()
	return(anchorDict,pageDict)

def getURI(anchorDict,pageDict,searchTerm):
	try:
		URI = pageDict[anchorDict[searchTerm]]
	except:
		URI = "Geen URI gevonden."
	return(URI)

def getProp(Xvalue):
	propreties = {
					'geloof':'prop-nl:geloof',
					'beroep':'dbpedia-owl:occupation',
					'naam':'dbpedia-owl:longName',
					'geboortedatum':'dbpedia-owl:birthDate',
					'genre':'dbpedia-owl:genre',
					'uitgever':'dbpedia-owl:publisher',
					'bijnaam':'prop-nl:bijnaam',
					'beginjaar':'prop-nl:jarenActief',
					'leden':'dbpedia-owl:bandMember',
					'functies':'dbpedia-owl:personFunction',
					'schreef':'dbpedia-owl:musicalArtist',
					'geschreven':'dbpedia-owl:musicalArtist',
					'auteur':'dbpedia-owl:musicalArtist',
					'componist':'dbpedia-owl:musicalArtist',
					'credits':'dbpedia-owl:musicalArtist',
					'speelde':'dbpedia-owl:bandMember',
					'bandlid':'dbpedia-owl:bandMember',
					'lid':'dbpedia-owl:bandMember'
					}
	proprety = propreties[Xvalue]
	return(proprety)

def getAnswer(URI,Prop):
	query = """
	PREFIX prop-nl: <http://nl.dbpedia.org/property/>
	PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
	SELECT DISTINCT STR(?answer)
	WHERE {
		<"""+URI+"""> """+Prop+""" ?answer
	} 
	"""
	sparql = SPARQLWrapper('http://nl.dbpedia.org/sparql')
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	answers = []
	for result in results["results"]["bindings"]:
		for arg in result :
			answer = result[arg]["value"]
			if answer[0:4] == "http":
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
						answers.append(answer)
			else:
				answers.append(answer)
	return(answers)

def main():
	# CSV bestanden initaliseren
	print("Een ogenblik geduld, de Wikipedia anchors worden geinitaliseerd.")
	anchorDict,pageDict = createDict('../../anchor_summary.csv','page.csv')

	questions = []
	data = sys.stdin
	if data.isatty() == True:
		questions = [
					"Wie is bandlid van U2?",
					"Welke personen was lid van de band U2?",
					"Wie speelde er in de band U2?",
					"Wie was een lid van de band U2?",
					"Geef de leden van U2",
					"Wie schreef het nummer I Will Follow?",
					"Wie heeft het nummer Sunday Bloody Sunday geschreven?",
					"Door wie werd het nummer The Saints Are Coming geschreven?",
					"Wie is de auteur van Desire?",
					"Geef de componist van Mysterious Ways",
					"Welke muzikant kreeg de credits voor het nummer Desire?",
					"Geef het geloof van Bono",
					"Wat is het geloof van Bono?",
					"Wat is het beroep van Bono?",
					"Wat is de naam van Gerard Joling?",
					"Wat is de geboortedatum van Jason Mraz?",
					"Wat is het genre van The Beatles?",
					"Wie is de uitgever van Marco Borsato?",
					"Wat is de bijnaam van Amy Winehouse?",
					"Wat is het beginjaar van Muse?",
					"Wie zijn de leden van The Beatles?",
					"Wat zijn de functies van Muse?"
					]
	else:
		for line in data:
				lineNew = re.sub('[\n]','',line)
				questions.append(line)

	for question in questions:
		# X en Y waarde berekenen
		Xvalue,Yvalue = analyzeSentence(question)

		if Xvalue == "Geen Xvalue gevonden" or Yvalue == "Geen Yvalue gevonden":
			print("De vraag kon niet worden geanalyseerd.")
		else:
			# URI opvragen
			URI = getURI(anchorDict,pageDict,Yvalue)

			# Proprety opvragen
			Prop = getProp(Xvalue)

			# Antwoord opvragen
			answers = getAnswer(URI,Prop)
			print("\n",question)
			try:
				for answer in answers:
					if answer !="":
						print(answer)
					else:
						print("Er zijn geen antwoorden gevonden.")
			except:
				print("Er zijn geen antwoorden gevonden.")
			print("")

if __name__ == '__main__':
    main()