#!/bin/bash
rm -rf ./LexConnex.app
cp -r build/osx_template.app ./LexConnex.app
cp -r processing-py.jar game.py gamestate.py lettertree.py libraries tweener.py wordlist_short data ./LexConnex.app/Contents/Resources/Java
