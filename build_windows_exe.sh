#!/bin/bash
LAUNCH4JPATH=/Users/adam/Downloads/launch4j
rm -rf build/Characterror.exe
rm -rf build/resources
mkdir build/resources
cp -r processing-py.jar game.py gamestate.py lettertree.py libraries tweener.py wordlist_short data build/resources
java -jar $LAUNCH4JPATH/launch4j.jar l4j.xml
