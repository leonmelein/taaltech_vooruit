# Taaltechnologie - Eindopdracht
# taaltech_vooruit
#!/usr/bin/env python3

# system packages needed to run the program
import csv
import socket
import sys
import os
import subprocess

# functions and classes to run the program
from find_relation import *
from exception_classes import *
from dbpedia_query import *
from alpino_parse import *

def main(question, anchors):
    # Parse and analyze question
    parse = parse_question(question)

    try:
        Concept, Property = analyze_question(parse)
        print("property: " + Property)
        wikiID = find_resource(Concept, anchors)

        if Property[0:7] == "hoeveel":
            relation = find_relation(Property[8:])
            answer = query(construct_query(wikiID, relation,"COUNT(?result)"))
        else:
            relation = find_relation(Property)
            answer = query(construct_query(wikiID, relation))

        answerList = output(answer)
        theList = [question] + answerList
        return theList

    except NoConceptException:
        print("No Concept")
        theList = [question] + ["No Concept"]
        return theList

    except NoPropertyException:
        print("No Property")
        theList = [question] + ["No Property"]
        return theList

    except NoPropertyRelationException:
        print("No relation")
        theList = [question] + ["No relation"]
        return theList

    except NoResultException:
        print("No results")
        theList = [question] + ["No results"]
        return theList

# three helper functions
def count_list(completeList):
    count = 0
    for question in completeList:
        if question[2] not in ["No results", "No Property", "No Concept", "No relation"]:
            count += 1
    print("\n" + str(round((count/len(completeList))*100, 2)) + "% answered.")

def write_out(completeList):
    thefile = open('fileout.txt', 'w')
    # create the tabs per question
    for i in range(len(completeList)):
        completeList[i] = '\t'.join(completeList[i])
    # writing all the questions with numbers and answers out
    for item in completeList:
        thefile.write("%s\n" % item)   

def open_file():
    print("Op Windows en Mac kun je het bestand direct openen!")
    yesOrNo = input("Output-bestand nu openen? (y/n) >> ")
    if "y" in yesOrNo.lower():

    	if sys.platform == 'linux2':
    		subprocess.call(["xdg-open", 'fileout.txt'])
    	else:
	        try:
	            os.system("open "+'fileout.txt')
	        except:
	            pass
	        try:
	            os.system("start "+'fileout.txt')
	        except:
	            pass


def load_anchors(file):
    with open(file, 'r') as f:
        reader = csv.reader(f)
        anchor = list(reader)
    return anchor

if __name__ == "__main__":
    anchors = load_anchors("../anchor_summary.csv")

    # Check for command-line argument
    if len(sys.argv) >= 2:
        completeList = []
        count = 1
        with open(sys.argv[1], 'r') as questions:
            for row in questions:
                try:
                    # if tab seperated values
                    question = (row.split("\t"))[1]
                except:
                    question = row
                while question[-1] == "\n" or question[-1] == " ":
                    question = question[:-1]
                print("\n" + question)
                theList = main(question, anchors)
                completeList.append([str(count)] + theList)
                count += 1
        count_list(completeList)
        write_out(completeList)
        open_file()
        

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

            # Run example questions
            if len(user_question) == 0:
                questions = ["Wat is de volledige naam van Anouk?",
                "Wat is de geboortedatum van Dries Roelvink?",
                "Wie zijn de leden van Muse?",
                "Wie zijn de voormalige leden van BZN?",
                "Wat is de website van Rihanna?",
                "Wat is het genre van Lady Gaga?",
                "Wat is het beroep van Bono?",
                "Wat zijn de platenmaatschappijen van de Kaiser Chiefs?",
                "Wat is de bezetting van The Wombats?",
                "Wat is de oorsprong van de Arctic Monkeys?",
                "Geef de website van The Wombats.",
                "Geef de volledige naam van Anouk.",
                "Welke genres bedient Lady Gaga?",
                "Welke leden heeft Muse?",
                "Wanneer is Dries Roelvink geboren?",
                "Wanneer is Anouk geboren?",
                "Hoe zijn The Wombats samengesteld?",
                "Hoe zijn de Kaiser Chiefs samengesteld?"]
                for question in questions:
                    print("\n" + question)
                    main(question, anchors)

            # Else, find the answer for the asked question
            else:
                main(user_question, anchors)

            # After the question has been handled, ask again.
            print("\n" + user_prompt)
            user_question = input(">> ")