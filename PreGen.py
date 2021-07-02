#!/usr/bin/env python
'''
 PreGen.py
 Process original authorlist from first publication to create list of legacy authors, affiliations and publicationNames
 in order to fulfill Bylaw 6.4 "All Members that have made a substantive contribution to the design and/or construction
 of the experiment will be an author on the first physics publication and the detector overview paper"
 Results from this script will then be added by hand to Detectorpaper/extra_authors_and_affiliations.txt
 20150501 D.Jaffe
 '''
infile = open('DYB_rate_prl.tex','r')
outfile= open('legacy_authors_affiliations_pubNames.txt','w')
for line in infile:
    if line[0]=='%':
        continue
    elif 'author' in line:
        print line[:-1]

infile.close()
outfile.close()
