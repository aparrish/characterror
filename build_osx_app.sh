#!/bin/bash
rm -rf build/osx
mkdir -p build/osx/Characterror
cp -r build_templates/osx_template.app build/osx/Characterror/Characterror.app
cp -r processing-py.jar game.py gamestate.py lettertree.py libraries tweener.py wordlist_short data build/osx/Characterror/Characterror.app/Contents/Resources/Java
cp -r README build/osx/Characterror
pushd build/osx
zip -r Characterror-osx.zip Characterror/*
popd
