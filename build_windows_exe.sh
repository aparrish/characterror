#!/bin/bash
LAUNCH4JPATH=/Users/adam/Downloads/launch4j
rm -rf build/win
mkdir -p build/win/Characterror/resources
cp -r processing-py.jar game.py gamestate.py lettertree.py libraries tweener.py wordlist_short data build/win/Characterror/resources
cp -r README build/win/Characterror
java -jar $LAUNCH4JPATH/launch4j.jar l4j.xml
pushd build/win
zip -r Characterror-win.zip Characterror/*
popd
