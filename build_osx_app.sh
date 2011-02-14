#!/bin/bash
rm -rf ./Characterror.app
cp -r build/osx_template.app ./Characterror.app
cp -r processing-py.jar game.py gamestate.py lettertree.py libraries tweener.py wordlist_short data ./Characterror.app/Contents/Resources/Java
