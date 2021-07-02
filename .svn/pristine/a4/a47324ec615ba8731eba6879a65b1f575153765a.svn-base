#!/usr/bin/env python
'''
 PreGen.py
 Process original authorlist from first publication to create list of legacy authors, affiliations and publicationNames
 in order to fulfill Bylaw 6.4 "All Members that have made a substantive contribution to the design and/or construction
 of the experiment will be an author on the first physics publication and the detector overview paper"
 Results from this script will then be added by hand to Detectorpaper/extra_authors_and_affiliations.txt
 20150501 D.Jaffe
 '''
def fixInst(Inst):
    '''
    return institution name as used list_with_pubnames.xls
    '''
    Pairs = { 'UW'     : 'Wisconsin',
              'JINR'   : 'Dubna',
              'PU'     : 'Princeton',
              'CIT'    : 'CalTech',
              'THU'    : 'TsingHue',
              'CU'     : 'Charles',
              'CGNPHC' : 'CGNPG',
              'VT'     : 'VirginiaTech',
              'UHK'    : 'HKU',
              'ISU'    : 'IowaState'}
    if Inst in Pairs: return Pairs[Inst]
    return Inst


### main starts here
debug = 0
infile = open('DYB_rate_prl.tex','r')
laap = 'legacy_authors_affiliations_pubNames.txt'
outfile= open(laap,'w')
outfile.write('##### this is file ' + laap + ' \n')

### Removing these names by hand is the easiest way to go
### 20150803 Olshevskiy is preferred to Olshevski
InvalidNames = ['Gill', 'Tull',  'Wilhelmi', 'Worcester', 'Olshevski']


for line in infile:
    if line[0]=='%':
        continue
    elif 'author' in line:
        line = line.replace('\n','') # remove control character
        PubName = line.split('{')[1].split('}')[0]
        colInst = 2
        Dead = 'Deceased' in line # special processing for the dead
        if Dead: colInst = 3
        Institution = line.split('\\')[colInst]
        Inst = fixInst(Institution)
        FamilyName = PubName.split('~')[-1]
        if FamilyName in InvalidNames:
            print 'Intentionally removing invalid FamilyName',FamilyName,'(This is not an error)'
            continue
        if FamilyName=='Jr.': FamilyName = PubName.split('~')[-2] +'~'+PubName.split('~')[-1]
        GivenName  = PubName.replace(FamilyName,'')
        outline = 'ADD ' + FamilyName + ' ' + GivenName + ' ' + Inst + ' ' + PubName
        outfile.write(outline + ' \n')
        if debug: print line[:-1],'PubName',PubName,'Institution',Institution,outline
        if Dead:
            outline = 'ADD ' + FamilyName + ' ' + GivenName + ' ' + 'DEAD' + ' ' + PubName
            if debug: print outline
            outfile.write(outline+ ' \n')


infile.close()
outfile.close()
print 'Wrote',laap
