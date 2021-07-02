#!/usr/bin/env python
'''
merge minos and daya bay authorlist
'''
import datetime
import os
import sys
class merge():
    def __init__(self):
        self.dyb_file = 'PhysRev.tex'
        self.minos_file = 'minos-plus_feb2016.tex' #'minos_author_list.tex'
        self.merged_file = 'merged_minos_dyb_authors.tex'
        self.AffilList =  ['\\affiliation','\\altaffiliation']
        # replace DYB institute abbreviation with that of MINOS
        self.Replacements = { '\\UH': '\\Houston',
                              '\\LBNL': '\\Berkeley',
                              '\\CalTech':'\\Caltech',
                              '\\IowaState':'\\Iowa',
                              '\\WM':'\\WandM'}
        # do not use these author names. they are duplicates with different initials
        # format is key,value = bad, good
        self.troubleAuthors = {'C.~G.~White':'C.~White', 'J.~Ling':'J.~J.~Ling'}
        self.dybsym = '\\delta'
        self.minsym = '\\mu'
        return
    def IHEP(self,com,authors,authorwithaffil):
        '''
        "\IHEP" latex command inadvertantly used for IHEP, Beijing and IHEP, Protvino
        Change to \CNIHEP for Beijing
        20161007
        '''
        oldAffil = '\IHEP'
        newAffil = '\CNIHEP'
        if oldAffil in com:
            value = com[oldAffil]
            if 'Beijing' not in value:
                sys.exit('merge.IHEP ERROR wrong value ' + value + ' for key ' + oldAffil)
            del com[oldAffil]
            com[newAffil] = value
            print 'merge.IHEP replace key',oldAffil,'with',newAffil,'for value',com[newAffil]
        n = 0
        for author in authors:
            affils = authorwithaffil[author] # can have multiple affiliations
            for affil in affils:
                if affil==oldAffil:
                    n += 1
                    affils.remove(oldAffil)
                    affils.append(newAffil)
            authorwithaffil[author] = affils
        print 'merge.IHEP replaced latex',oldAffil,'with',newAffil,'for',n,'authors'
        return com,authors,authorwithaffil
    def Main(self):

        debug = 0
        
        # parse original minos author list
        MINOS_NewCom,MINOS_Authors,MINOS_AuthorWithAffil = self.readFile(self.minos_file)
        if debug>1: self.printCom(MINOS_NewCom,'MINOS_NewCom')

        # parse original dyb author list
        DYB_NewCom,  DYB_Authors,  DYB_AuthorWithAffil   = self.readFile(self.dyb_file)
        if debug>1: self.printCom(DYB_NewCom,'DYB_NewCom before IHEP fix')
        DYB_NewCom, DYB_Authors, DYB_AuthorWithAffil = self.IHEP(DYB_NewCom, DYB_Authors, DYB_AuthorWithAffil)
        if debug>1: self.printCom(DYB_NewCom,'DYB_NewCom AFTER IHEP fix')
        
            

        # report authors with affiliation
        if debug>1: 
            self.listAffil(MINOS_AuthorWithAffil, 'MINOS')
            self.listAffil(DYB_AuthorWithAffil, 'DYB')

        # fix dyb authors with affiliation to match MINOS
        DYB_AuthorWithAffil = self.fixDybAffil(DYB_NewCom, DYB_AuthorWithAffil)
        if debug>1:
            self.listAffil(DYB_AuthorWithAffil,'DYB after fix')

        # merge dicts of commands that define address of each institution
        NewCom = self.mergeCom(MINOS_NewCom, DYB_NewCom)
        if debug>1: self.printCom(NewCom,'NewCom after merger')

        # list duplicate authors
        if debug>-1:
            self.findDuplicates(MINOS_AuthorWithAffil, DYB_AuthorWithAffil)
            
        authorLatex,authorList = self.makeAuthorLatex(MINOS_AuthorWithAffil, DYB_AuthorWithAffil)
        if debug>0: 
            print '\n authorLatex'
            for author in authorList: print author,authorLatex[author][:-1] # don't print carriage return

        self.writeAuthorList(NewCom,authorLatex,authorList)

        print '\n Press return to test authorlist and generate pdf'
        raw_input()

        cmd = 'pdflatex test_combined_authorlist ; bibtex test_combined_authorlist; pdflatex  test_combined_authorlist ; pdflatex  test_combined_authorlist'
        os.system(cmd)
        print '\n Tested author list by executing',cmd,'\n'
            
        return
    def writeAuthorList(self,NewCom,authorLatex,authorList):
        '''
        write merged institutions and authors to file
        '''
        f = open(self.merged_file,'w')

        args = ''
        for a in sys.argv: args += a + ' '
        genInfo = ['Generator info for file',datetime.datetime.now().ctime(), os.getcwd(), args]
        for a in genInfo:
            f.write('%%%% ' + a + '\n')
        f.write('%\n')
        for VAR in NewCom:
            f.write('\\newcommand{'+VAR+'}'+NewCom[VAR] + '\n')
        f.write('%\n')
        for author in authorList :
            f.write(authorLatex[author])
        f.write('%\n')
        f.write('\\collaboration{\\ensuremath{^{'+self.dybsym+'}}Daya Bay Collaboration}\\noaffiliation\n')
        f.write('\\collaboration{\\ensuremath{^{'+self.minsym+'}}MINOS Collaboration}\\noaffiliation\n')
        f.close()
        print 'writeAuthorList: wrote to',self.merged_file
        
    def printCom(self,COM,words=''):
        print '\n',words
        for VAR in sorted(COM): print VAR,COM[VAR]
        return
    def mergeCom(self,MINOS,DYB):
        '''
        return dict with merger of MINOS, DYB dicts containing institutions.
        key,value = institution abbreviation,institution address
        also perform some fixes
        '''
        notify = False
        newCom = {}
        for M in MINOS:
            if M in DYB:
                if notify: print 'mergeCom:M',M,'MINOS[M]',MINOS[M],'DYB[M]',DYB[M]
            newCom[M] = MINOS[M]
        for M in DYB:
            if M not in MINOS and M not in self.Replacements:
                for aff in self.AffilList:
                    if aff in DYB[M]: newCom[M] = DYB[M].replace(aff,'')
                        
        # fixes
        # Place the 'now at' into the institution name
        for M in newCom:
            if '[Now at ]{D' in newCom[M]: newCom[M] = newCom[M].replace('[Now at ]{D','{Now at D')
        return newCom
    def slasher(self,s):
        '''
        from string of form '\XXX\ABC\YYY' return list ['\XXX','\ABC','\YYY']
        '''
        slash = '\\'
        l = []
        i = s.find(slash)
        while i<len(s) and i>-1:
            i2 = s[i+1:].find(slash)
            if i2==-1: i2=len(s)
            l.append( s[i:i+1+i2] )
            i += i2+1
        return l
    def fixDybAffil(self,NewCom,AuthorWithAffil):
        '''
        return new DYB author with affiliation same as MINOS
        '''
        newAWA = {}
        for author in AuthorWithAffil:
            newAWA[author] = []
            for aff in AuthorWithAffil[author]:
                alist = self.slasher(aff) # have to parse multiple backslashes
            blist = []
            for aff in alist:
                if aff in self.Replacements:
                    blist.append( self.Replacements[aff] )
                else:
                    blist.append( aff )
            alist = blist
            for aff in alist:
                inst = NewCom[aff]
                for X in self.AffilList:
                    if X in inst:
                        newAWA[author].append(X+'{'+aff+'}')
        return newAWA
    def makeAuthorLatex(self,MINOS,DYB):
        '''
        return a dict with key=authorname value=latex and an alphabetic list of authors
        include all unique affiliations for duplicate authors
        '''
        authorList = self.makeSingleList(MINOS,DYB,IncludeDuplicates=False)
        authorLatex = {}
        for author in authorList:
            words = '\\author{' + author
            if author in DYB: words += '\\ensuremath{^{'+self.dybsym+'}}'
            if author in MINOS: words += '\\ensuremath{^{'+self.minsym+'}}'
            words += '}\n' ###
            if author in DYB:
                for aff in DYB[author]: words += aff
            if author in MINOS:
                for aff in MINOS[author]:
                    if aff not in words: words += aff
# original                    
#            if author in DYB and author not in MINOS:
#                for aff in DYB[author]: words += aff
#            if author in MINOS:
#                for aff in MINOS[author]: words += aff
            words += ' \n'
            authorLatex[author] = words
        return authorLatex,authorList
    def parseAuthorName(self,author):
        '''
        X.~Y.~Jones is parsed as firstName = 'X.~Y.', lastName = 'Jones'
        20160624 deal with special case for S.~De~Rijck
        '''
        lastName = author.split('~')[-1]
        firstName = author.replace('~'+lastName,'')
        if author=='S.~De~Rijck':  
            lastName = 'De Rijck'
            firstName = 'S.'
        return firstName,lastName
    def makeSingleList(self,MINOS,DYB,IncludeDuplicates=True):
        '''
        return single, alphabetized list of all authors INCLUDING DUPLICATES, if requested
        '''
        alist = MINOS.keys()
        alist.extend( DYB.keys() )

        sortedList = sorted(alist, key=lambda s: (self.parseAuthorName(s)[1] +' '+ self.parseAuthorName(s)[0]).lower())
        
        if not IncludeDuplicates:
            alist = []
            for i,author in enumerate(sortedList):
                if i+1<len(sortedList):
                    if author!=sortedList[i+1]: alist.append(author)
            sortedList = alist
        return sortedList
    def findDuplicates(self,MINOS,DYB):
        '''
        locate duplicate authors by comparing keys from two dicts
        '''
        for author in MINOS:
            if author in DYB:
                print 'Affiliations for duplicate author',author,'MINOS:',MINOS[author],'DYB:',DYB[author]
        if 0:
            print '\n Combined authorlist alphabetized:'
            sortedList = self.makeSingleList(MINOS,DYB)
            for author in sortedList:
                print author,
                if author in MINOS:
                    print MINOS[author],
                if author in DYB:
                    print DYB[author],
                print ''
            
        return
    def listAffil(self, AuthorWithAffil,title=''):
        '''
        simple printout of author and affiliations
        '''
        #print AuthorWithAffil
        print '\n',title,'Author with Affiliation'
        for author in AuthorWithAffil:
            print author,
            for x in AuthorWithAffil[author]: print x,
            print ''
        return 
    def firstCommand(self,line):
        '''
        return first latex-style command in line
        '''
        if '{' in line and '\\' in line:
            return line.split('{')[0]
        else:
            return None
    def readFile(self,fn):
        '''
        read and process file with original author lists
        special treatment for duplicate institutions and duplicate authors
        '''
        f = open(fn,'r')
        NewCom = {}
        Authors= []
        CurrentAuthor = None
        AuthorWithAffil = {}
        AffilList = self.AffilList
        for line in f:
            if line[0]=='%' or line in ['\n','\r\n']: # no blank or comment lines
                pass
            else:
                latexCommand = self.firstCommand(line)
                cleanline = line.replace('\r','').replace('\n','')
                if latexCommand=='\\newcommand':
                    VAR = cleanline.split('{')[1].split('}')[0]
                    COM = cleanline.split('}',1)[1]
                    if VAR in self.Replacements: VAR = self.Replacements[VAR]  
                    NewCom[VAR] = COM
                elif latexCommand=='\\author':
                    # 20160523 deal with author names with special characters
                    if line.count('}')==1:
                        AuthorName = line.split('{')[1].split('}')[0]
                        GetAffil = True
                    else:
                        i2 = line.rfind('}')
                        i1 = line.find('{')
                        AuthorName = line[i1+1:i2]
                        GetAffil = False
                    if AuthorName in self.troubleAuthors: AuthorName = self.troubleAuthors[AuthorName]
                    CurrentAuthor = AuthorName
                    Authors.append(AuthorName)
                    AuthorWithAffil[AuthorName] = []
                    if GetAffil:
                        Affil = cleanline.split('}')[1]
                        if Affil!='':
                            AuthorWithAffil[AuthorName] = [Affil] # dyb style
                elif latexCommand in AffilList:  # minos style
                    if CurrentAuthor in AuthorWithAffil:
                        AuthorWithAffil[CurrentAuthor].append(cleanline)
        f.close()
        return NewCom, Authors, AuthorWithAffil



if __name__ == '__main__':
    m = merge()
    m.Main()
