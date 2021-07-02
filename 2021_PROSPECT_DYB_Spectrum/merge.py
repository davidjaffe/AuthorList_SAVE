#!/usr/bin/env python
'''
merge minos and daya bay authorlist

20190819 kludge to deal with Daya Bay authors with identical latex author names
20190823 add USA to Daya Bay institutions where appropriate
20210406 copy from 2019_MINOS_DYB_sterile/ to 2021_PROSPECT_DYB_Spectrum/ , and modify.
          retain 'minos' or similar for non-DYB
'''
import datetime
import os
import sys
class merge():
    def __init__(self,debug=-1):
        self.debug = debug
        self.dyb_file = 'PhysRev.tex'
        self.PROSPECT_orig_file = 'PROSPECT_AuthorListApril2021.tex'
        self.minos_file = 'fixed_' + self.PROSPECT_orig_file #'minos-plus_jul2019.tex' #'minos-plus_feb2016.tex' #'minos_author_list.tex'
        self.merged_file = 'merged_prospect_dyb_authors.tex'
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
        self.minsym = '\\pi'
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
            #print 'merge.IHEP replace key',oldAffil,'with',newAffil,'for value',com[newAffil]
        n = 0
        for author in authors:
            #if 'Grass' in author: print 'merge.IHEP oldAffil,author,authorwithaffil[author]',oldAffil,author,authorwithaffil[author]
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

        # fix original PROSPECT author list
        self.fixPROSPECTfile(self.PROSPECT_orig_file, self.minos_file,debug=debug)

        debug = self.debug
        
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

        # 20190823 add USA, Czech Republic, Russia to institutions where appropriate
        NewCom = self.fixCountry(NewCom)
        if debug>1: self.printCom(NewCom,'NewCom after fixing country name')

        # list duplicate authors
        if debug>-1:
            self.findDuplicates(MINOS_AuthorWithAffil, DYB_AuthorWithAffil)
            
        authorLatex,authorList = self.makeAuthorLatex(MINOS_AuthorWithAffil, DYB_AuthorWithAffil)
        if debug>0: 
            print '\n authorLatex'
            for author in authorList: print author,authorLatex[author][:-1] # don't print carriage return

        self.writeAuthorList(NewCom,authorLatex,authorList)

        if debug>0: sys.exit('merge.Main ****** NO TEST OF AUTHORLIST CUZ YOU ARE DEBUGGING *****')

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
        f.write('\\collaboration{\\ensuremath{^{'+self.minsym+'}}PROSPECT Collaboration}\\noaffiliation\n')
        f.close()
        print 'writeAuthorList: wrote to',self.merged_file
        
    def printCom(self,COM,words=''):
        print '\n',words
        for VAR in sorted(COM): print VAR,COM[VAR]
        return
    def fixCountry(self,COM):
        '''
        20190823         
        add USA to affiliation where appropriate.
        Only consider states that are in the current list of affiliations
        20210407
        also add Czechia, Russia
        '''
        self.states = {'USA': ['Iowa','Connecticut','Illinois','Pennsylvania','New~Jersey','Ohio','New York','California','Virginia'],
                           'Czech Republic' : ['Prague'],
                           'Russia'  : ['Moscow']
                           }
        newCom = {}
        for M in COM:
            affil = COM[M]
            for country in self.states:
                for state in self.states[country]:
                    if state in affil:
                        if country not in affil:
                            affil = affil.replace('}}',', '+country+'}}')
                            break
                newCom[M] = affil
        return newCom
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
                    if aff in DYB[M]: newCom[M] = DYB[M] ######.replace(aff,'')
                        
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
        debug = False
        if debug :
            print 'merge.fixDybAffil NewCom',NewCom
            print 'merge.fixDybAffil AuthorWithAffil',AuthorWithAffil
            
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
            if debug : print 'merge.fixDybAffil author,alist',author,alist
            for aff in alist:
                inst = NewCom[aff]
                for X in self.AffilList:
                    if X in inst:
#                        newAWA[author].append(X+'{'+aff+'}')
                        newAWA[author].append(aff)
        return newAWA
    def makeAuthorLatex(self,MINOS,DYB):
        '''
        return a dict with key=authorname value=latex and an alphabetic list of authors
        include all unique affiliations for duplicate authors
        20190821 kludge for authors with identical latex names
        '''
        authorList = self.makeSingleList(MINOS,DYB,IncludeDuplicates=False)
        if self.debug > 1 : print 'merge.makeAuthorLatex after makeSingleList authorList is',authorList
        authorLatex = {}
        for author in authorList:
            theAuthor = author
            if '0' in author: theAuthor = author[:author.find('0')]
            words = '\\author{' + theAuthor
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
        20190821 deal with identical latex names
        '''
        lastName = author.split('~')[-1]
        if '0' in lastName: lastName = lastName[:lastName.find('0')]
        firstName = author.replace('~'+lastName,'')
        if author=='S.~De~Rijck':  
            lastName = 'De Rijck'
            firstName = 'S.'
        return firstName,lastName
    def makeSingleList(self,MINOS,DYB,IncludeDuplicates=True):
        '''
        return single, alphabetized list of all authors INCLUDING DUPLICATES, if requested
        20210408 fix to ensure last author on list is included, if not a duplicate
        '''
        alist = MINOS.keys()
        alist.extend( DYB.keys() )
        if self.debug > 1 : print 'merge.makeSingleList alist',alist

        sortedList = sorted(alist, key=lambda s: (self.parseAuthorName(s)[1] +' '+ self.parseAuthorName(s)[0]).lower())

        if self.debug > 1 : print 'merge.makeSingleList sortedList',sortedList
        
        if not IncludeDuplicates:
            alist = []
            for i,author in enumerate(sortedList):
                if i+1<len(sortedList):
                    if author!=sortedList[i+1]: alist.append(author)
                else:
                    if author!=sortedList[i-1]: alist.append(author)
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
    def fixPROSPECTfile(self,fn,fnout,debug=-1):
        '''
        read in PROSPECT author list and produce new file where affiliations are defined by acronyms
        using \newcommand to make it easier to merge the two authorlists

        Paff is a dict with key=acronym and value=affiliation. keys will be used to create \newcommand and will match DYB, if appropriate. 
        '''
        Paff = {"BNL":         "\\affiliation{Brookhaven National Laboratory, Upton, NY, USA}",
                "Drexel":"\\affiliation{Department of Physics, Drexel University, Philadelphia, PA, USA}",
                "GATECH":"\\affiliation{George W.\,Woodruff School of Mechanical Engineering, Georgia Institute of Technology, Atlanta, GA USA}",
                "Hawaii" : "\\affiliation{Department of Physics \& Astronomy, University of Hawaii, Honolulu, HI, USA}",
                "IIT": "\\affiliation{Department of Physics, Illinois Institute of Technology, Chicago, IL, USA}",
                "LLNL":"\\affiliation{Nuclear and Chemical Sciences Division, Lawrence Livermore National Laboratory, Livermore, CA, USA}",
                "LeMoyne":"\\affiliation{Department of Physics, Le Moyne College, Syracuse, NY, USA}",
                "NIST":"\\affiliation{National Institute of Standards and Technology, Gaithersburg, MD, USA}",
                "HFIR":"\\affiliation{High Flux Isotope Reactor, Oak Ridge National Laboratory, Oak Ridge, TN, USA}",
                "ORNL":"\\affiliation{Physics Division, Oak Ridge National Laboratory, Oak Ridge, TN, USA}",
                "TempleUniversity" : "\\affiliation{Department of Physics, Temple University, Philadelphia, PA, USA}",
                "TENN":"\\affiliation{Department of Physics and Astronomy, University of Tennessee, Knoxville, TN, USA}",
                "Waterloo":"\\affiliation{Institute for Quantum Computing and Department of Physics and Astronomy, University of Waterloo, Waterloo, ON, Canada}",
                "Wisconsin" : "\\affiliation{Department of Physics, University of Wisconsin, Madison, Madison, WI, USA}",
                "Yale" : "\\affiliation{Wright Laboratory, Department of Physics, Yale University, New Haven, CT, USA}" }
        f = open(fn,'r')
        NewCom = {}
        AuthorAff = {}
        doneWithAff = False
        lines = f.read().splitlines() 
        for i in range(len(lines)):
            line = lines[i]
            nextline = ''
            if i+1 < len(lines) : nextline = lines[i+1]
            if debug > 0 : print 'merge.fixPROSPECTfile doneWithAff,line,nextline',doneWithAff,line,nextline[:-1]
            if not doneWithAff :
                if line==' ' or 'affiliation' not in line:
                    doneWithAff = True
            if not doneWithAff : # process one way
                key = self.findKey(line,Paff)
                if key is not None:
                    NewCom[key] = '\\newcommand{\\'+key+'}{'+Paff[key]+'}\n'
                else :
                    sys.exit('merge.fixPROSPECTfile ERROR Could not find line '+line)
            else:
                if 'author' in line:
                    LINE = line
                    if 'affiliation' in nextline and 'author' not in nextline: LINE += nextline
                    author,value = self.setAff(LINE,Paff) 
                    AuthorAff[author] = value + '\n'
        f.close()
        
        f = open(fnout,'w')
        for key in sorted(NewCom):
            if debug > 0 : print 'merge.fixPROSPECTfile key,NewCom[key]',key,NewCom[key]
            f.write(NewCom[key])
        for author in AuthorAff:
            if debug > 0 : print 'merge.fixPROSPECTfile author,AuthorAff[author]',author,AuthorAff[author]
            f.write(author + AuthorAff[author])
        f.close()
    def setAff(self,line,Paff):
        '''
        parse line to find all the \affiliation{blah-blah} instances, 
        find key in Paff such that Paff[key]=blah-blah,
        return line with blah-blah replaced with key for all instances
        '''
        debug = -1
        newline = line.replace('\x07','\\a')
        if debug>0 : print 'merge.setAff newline',newline
        if debug>1 : print 'merge.setAff newline.split',newline.split('\\')
        author = newline[:newline.find('}')+1].replace('\\,','~') # make same as DYB 
        affs = []
        sL = self.sepLine(newline)
        if debug>0 : print 'merge.setAff sL',sL
        for oword in sL:
            word = (oword).strip() # remove whitespace
            if debug>0: print 'merge.setAff word',word
            if 'affiliation' in word:
                for key in Paff:
                    if debug>1 : print 'merge.setAff key,Paff[key]',key,Paff[key]
                    matches = sum(a==b for a,b in zip(word,Paff[key]))
                    l1,l2 = len(word),len(Paff[key])
                    if debug>1 : print 'merge.setAff matches,l1,l2',matches,l1,l2
                    if word in Paff[key] or word==Paff[key]:
                        if debug>0 : print 'merge.setAff key,word,Paff[key]',key,word,Paff[key]
                        affs.append(key)
                        
        if debug>0 : print 'merge.setAff affs',affs
        value = ''
        for x in affs:
            value += '\\'+x
        if debug>0 : print 'merge.setAff author,value',author,value
        return author,value
    def sepLine(self,line):
        '''
        for line  = '\aa{bb cc}\dd{ee}\ff{g h i}'
        return ['\aa{bb cc}','\dd{ee}', '\ff{g h i}']
        '''
        s = []
        while len(line)>0:
            l1 = line.find('\\')
            if l1<0 : break
            l2 = line.find('}')
            if l2<0 : break
            x = line[l1:l2+1]
            s.append(x)
            line = line[l2+1:]
        return s
    def findKey(self,line,Paff):
        '''
        return key for value in dict Paff that matches line
        otherwise return None
        '''
        debug = -1
        OK = False
        if debug > 0 : print 'merge.findKey xlinex','x'+line+'x'
        for key in Paff:
            if debug > 0 : print 'merge.findKey key,xPaff[key]x',key,'x'+Paff[key]+'x'
            if Paff[key] in line:
                return key
        return None
    def readFile(self,fn):
        '''
        read and process file with original author lists
        special treatment for duplicate institutions and duplicate authors
        extra special treatment for authors with identical latex author names
        '''
        f = open(fn,'r')
        NewCom = {}
        Authors= []
        CurrentAuthor = None
        AuthorWithAffil = {}
        AffilList = self.AffilList
        identicalAuthors = {}
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
                    if AuthorName in AuthorWithAffil: # duplicate name? 20190821
                        print 'merge.readFile: AuthorName',AuthorName,'already appears in AuthorWithAffil as',AuthorWithAffil[AuthorName]
                        if AuthorName in identicalAuthors:
                            identicalAuthors[AuthorName] += 1
                        else:
                            identicalAuthors[AuthorName] = 1
                        AuthorName += '0' + str(identicalAuthors[AuthorName])
                        print 'merge.readFile: Created kludged AuthorName',AuthorName,'to deal with identical author name'
                            
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
    debug = -1
    if len(sys.argv)>1 : debug=int(sys.argv[1])
    m = merge(debug=debug)
    m.Main()
