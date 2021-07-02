#!/bin/bash

function get-list-of-author-paper-name() {
    xsltproc get_papername.xsl authors.xml > autogen-author-paper-name.txt
}

function get-list-of-org-paper-name() {
    xsltproc get_affils.xsl authors.xml > autogen-org-paper-name.txt
}

function list-who-is-not-there() {
    python main.py
}

#############################################################################
# alias name
#############################################################################
function apn() { get-list-of-author-paper-name; }
function opn() { get-list-of-org-paper-name; }

function main() {
    apn
    opn
    list-who-is-not-there
}
if [ -z "$*" ]; then
    main
else
    $*
fi
