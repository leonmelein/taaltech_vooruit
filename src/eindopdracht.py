# Taaltechnologie - Eindopdracht
# taaltech_vooruit
#!/usr/bin/env python3

# system packages needed to run the program
import csv
import socket
import sys

# functions and classes to run the program
from find_relation import *
from exception_classes import *
from dbpedia_query import *
from alpino_parse import *

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

# import the anchors file
def load_anchors(file):
    with open(file, 'r') as f:
        reader = csv.reader(f)
        anchor = list(reader)
    return anchor

def main(question, anchors):
    # Parse and analyze question
    parse = parse_question(question)

    try:
        Concept, Property = analyze_question(parse)

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
                print(question)
                theList = main(question, anchors)
                theList = [str(count)] + theList
                completeList.append(theList)
                count += 1
        count_list(completeList)
        write_out(completeList)

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
                main("Wat is het beroep van Bono?", anchors)
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