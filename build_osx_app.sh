#!/bin/bash
rm -rf build/Characterror.app
cp -r build_templates/osx_template.app build/Characterror.app
cp -r processing-py.jar game.py gamestate.py lettertree.py libraries tweener.py wordlist_short data build/Characterror.app/Contents/Resources/Java
