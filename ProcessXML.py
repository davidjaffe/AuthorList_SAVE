#!/usr/bin/env python
'''
Process an XML file to create a new xml file
20160607 D.Jaffe
'''
from lxml import etree
import os.path
import os


class ProcessXML():
    def __init__(self):
        self.xml  = None
        self.tree = None
        self.root = None
        self.context = None

        self.schemaFileName = None
        self.schema = None
        
# namespaces
#<collaborationauthorlist xmlns:cal="http://www.slac.stanford.edu/spires/hepnames/authors_xml/" xmlns:foaf="http://xmlns.com/foaf/0.1/">
        self.ns   = {'cal': "http://www.slac.stanford.edu/spires/hepnames/authors_xml/",
                     'foaf': "http://xmlns.com/foaf/0.1/"
                     }
        self.CAL_NS = self.ns['cal']
        self.FOAF_NS= self.ns['foaf']

        self.originalXML = '../nGd_Long_2016/authors.xml'
        self.INSPIREIDs = None
        
        print 'ProcessXML Initialized'
        return
    def open(self,fn):
        '''
        open xml file
        '''
        if not os.path.isfile(fn):
            import sys
            sys.exit('ProcessXML.open ERROR ' + fn + ' DOES NOT EXIST')
        
        self.tree = etree.parse(fn)
        self.root = self.tree.getroot()
        self.context = etree.iterparse(fn)
        self.etree = etree

        if self.schemaFileName is not None:
            self.schema = etree.XMLSchema( etree.parse( self.schemaFileName ) )
        print 'ProcessXML.open Opened',fn

        #### testing stuff...
        if 0:
            for action,elem in self.context:
                if not elem.text:
                    text = "None"
                else:
                    text = elem.text
                print elem.tag + " => " + text
            return
    def setSchemaFile(self,fn='authors.xsd'):
        '''
        set schema file for validation
        '''
        self.schemaFileName = fn
        return 
    def getPerson(self,authorName,orgs=None,debug=False):
        '''
        get xml Person entry for this authorName
        disambiguate with list of affiliations orgs, if provided
        '''
        if debug: print 'ProcessXML.getPerson inputs',authorName,orgs
        people = self.getPeople(authorName,orgs=orgs,debug=debug)
        if len(people)==1: return people[0]
        return None
    def getPeople(self,authorName,orgs=None,debug=False):
        '''
        return list of all xml Person entries for this authorName
        disambiguate with list of affiliations orgs, if provided
        '''
        if debug: print 'ProcessXML.getPeople input',authorName
        people = []
        for aName in self.tree.xpath('/collaborationauthorlist/cal:authors/foaf:Person/cal:authorNamePaper',namespaces=self.ns):
            if aName.text==authorName :
                if debug: print 'ProcessXML.getPeople aName:',aName,' text:',aName.text,' tag:',aName.tag,' attrib:',aName.attrib
                parent = aName.getparent()
                if debug: print 'ProcessXML.getPeople parent',parent
                if orgs is not None:
                    ids = self.getPersonOrgID(parent)
                    if debug: print 'ProcessXML.getPeople ids for parent',ids
                    if len(set(ids).intersection(orgs))>0 : people.append(parent)
                else:
                    people.append(parent)
        return people
                
        
    def getInst(self,instName,debug=False):
        '''
        get xml Organization entry for this institution name instName
        instName can be string or a list of strings
        preferred (most robust) method is to match a list of strings
        '''
        if debug: print 'ProcessXML.getInst try to match',instName
            
        if type(instName) is not list:
            matches = []
            for org in self.tree.xpath('/collaborationauthorlist/cal:organizations/foaf:Organization',namespaces=self.ns):
                for child in org.getchildren():
                    if debug: print 'ProcessXML.getInst child',child,'\n tag',''.join(child.tag).encode('utf-8'),\
                        '\n attrib',''.join(child.attrib).encode('utf-8'),'\n text',''.join(child.text).encode('utf-8')
                    if instName.lower() in child.text.lower():
                        if org not in matches: matches.append(org)

            if len(matches)==1: return matches[0]

            if len(matches)>1 or debug:
                print 'ProcessXML.getInst found',len(matches),'matches for',instName
                newmatches = []
                for match in matches:
                    for child in match.getchildren():
                        if instName in child.text:
                            newmatches.append( match )
                print 'ProcessXML.getInst winnowed, found',len(newmatches),'new matches for',instName
                if len(newmatches): return newmatches[0]

                for match in matches:
                    print '\n match',match,'text',match.text,'tag',match.tag
                    for child in match.getchildren():
                        print '\n child',child,'\n child.text',child.text,'\n child.tag',child.tag
        else:
            # try for best match of input address with words in orgAddress
            # remove zero-length strings before comparison
            # if more than one best match, try weighted, reverse order comparison
            if debug: print 'ProcessXML.getInst instName',instName
            iA = []
            for i in instName:
                if len(i)>0: iA.append(i)

            matches = {}
            orgDict = {}
            for org in self.tree.xpath('/collaborationauthorlist/cal:organizations/foaf:Organization/cal:orgAddress',namespaces=self.ns):
                oA = []
                for o in org.text.replace(',',' ').split(' '):
                    if len(o)>0: oA.append(o)
                orgDict[org] = oA
                matches[org] = len(set(iA).intersection(oA))
            best,Lbest = None,-1
            for org in matches:
                if matches[org]>Lbest:
                    Lbest = matches[org]
                    best = org
            # check if first and second best match are same
            #list best 4 matches in reverse order. 
            n = 4
            first = second = None
            for x in sorted( matches, key=matches.get, reverse=True):
                if debug and n>0:  print 'ProcessXML.getInst nmatch',matches[x],'text',x.text
                if first is not None and second is None: second = matches[x]
                if first is None: first = matches[x]
                n -= 1

            if first!=second: return best.getparent()  # Success!

            # now try weighted, reverse order comparison
            matches = {}
            for org in orgDict:
                oA = orgDict[org]
                wt = 0
                for i in reversed(iA):
                    if i in oA: wt += iA.index(i)
                matches[org] = wt
            best,Lbest = None, -1
            for org in matches:
                if matches[org]>Lbest:
                    Lbest = matches[org]
                    best = org
            # check if first and second best match are same
            #list best 4 matches in reverse order. 
            n = 4
            first = second = None
            for x in sorted( matches, key=matches.get, reverse=True):
                if debug and n>0:  print 'ProcessXML.getInst weight',matches[x],'text',x.text
                if first is not None and second is None: second = matches[x]
                if first is None: first = matches[x]
                n -= 1

            if first!=second: return best.getparent()  # Success!
                    

        return None
    def getOrgID(self,org):
        ''' return organization id given xml of organization '''
        return org.get('id')
    def getOrgName(self,org):
        ''' return name of organization given xml '''
        return         org.findtext(etree.QName(self.FOAF_NS,'name'),namespaces=self.ns)
    def getAddressWords(self,address):
        '''
        return list of words in address. Remove punctuation, remove ties
        '''
        A = address.replace(',',' ').replace('~',' ').split(' ')
        l = []
        for x in A:
            if x!='': l.append(x)
        return l
    def getNC(self,fn='PhysRev.tex'):
        '''
        returns list of 'newcommand' lines to get institution matches
        '''
        f = open(fn,'r')
        instDict = {}
        for line in f:
            if 'newcommand' in line:
                a = line.replace('\\newcommand','').replace('\x07ffiliation','').replace('\\','').replace('affiliation','').split('}')
                key = a[0].replace('{','')
                value = a[1].replace('{','').replace('~',' ')
                if key in instDict:
                    print 'error key',key,'already in instDict',instDict[key]
                instDict[key] = value
        f.close()
        return instDict
    def getPersonAuthorID(self,person):
        '''
        get author id(s) given xml element for person
        '''
        IDs = []

        for child in person.iterdescendants():
            if child.tag==etree.QName(self.CAL_NS,'authorid') :
                IDs.append( child.text )
        return IDs
    def foundPersonAuthorID(self,person,value = None):
        '''
        return xml authorid element if value matches the value of the 'source' attribute of an authorid given xml element for person
        '''
        if value is None: return None
        for child in person.iterdescendants():
            if child.tag==etree.QName(self.CAL_NS,'authorid'):
                #print 'ProcessXML.foundPersonAuthorID child.attrib',child.attrib
                for k in child.attrib:
                    v = child.attrib[k]
                    if k=='source' and v==value: return child
        return None
    def getAuthorIDsElement(self,person):
        '''
        get element with tag 'authorids'
        '''
        for child in person.iterdescendants():
            if child.tag==etree.QName(self.CAL_NS,'authorids'): return child
        return None
    def getAuthorName(self,person):
        '''
        return authorname given xml person
        '''
        for child in person.iterdescendants():
            if child.tag==etree.QName(self.CAL_NS,'authorNamePaper'): return child.text.strip()
        return None
    def getGivenName(self,person):
        for child in person.iterdescendants():
            if child.tag==etree.QName(self.FOAF_NS,'givenName'): return child.text.strip()
        return None
    def getFamilyName(self,person):
        for child in person.iterdescendants():
            if child.tag==etree.QName(self.FOAF_NS,'familyName'): return child.text.strip()
        return None
    def getPersonOrgID(self,person):
        '''
        get organization id(s) given xml element for person
        '''
        IDs = []
        for child in person.iterdescendants():
            oid = child.get('organizationid')
            if oid is not None: IDs.append(oid)
        return IDs
    def tostring(self,element):
        return etree.tostring(element)
    def cloneElement(self,element):
        ''' returns a copy of element '''
        return etree.fromstring( etree.tostring(element) )
    def makeNewElement(self,new_element,replacements=None,additions=None,removals=None, debug=False):
        '''
        return xml element using input new_element with structure
        use replacements to replace (overwrite) the information in the new element
        use additions to add new substructure to the new element. add new substructure of pre-existing substructure
        use removals to remove substructure from new element
        Otherwise reproduce original xml if nothing provided in replacements, additions, removals
        Note that only one instance will be replaced or removed, so that replacements of the
        same substructure require multiple calls
        '''

        if debug: print 'ProcessXML.makeNewElement replacements=',replacements,'\n additions=',additions,'\n removals=',removals
        

        if replacements is not None:
            if debug: print 'ProcessXML.makeNewElement replacements',replacements
            parentNkids = [new_element]
            for child in new_element.iterdescendants(): parentNkids.append(child)
            usedkeys = []
            for child in parentNkids: 
                for key in replacements:
                    if isinstance(replacements[key],list):
                        if key in child.attrib:
                            if replacements[key][0]==child.attrib[key]:
                                child.set(key,replacements[key][0])
                                child.text = replacements[key][1]
                                usedkeys.append(key)
                    else:
                        if key in child.tag:
                            if debug: print 'ProcessXML.makeNewElement found key',key,'in child.tag',child.tag,'replace with',replacements[key]
                            child.text = replacements[key]
                            usedkeys.append(key)
                        if key in child.attrib:
                            if debug: print 'ProcessXML.makeNewElement found key',key,'in child.attrib',child.attrib,'replace with',{key:replacements[key]}
                            child.set(key,replacements[key])
                            usedkeys.append(key)
                for key in usedkeys:
                    if key in replacements: del replacements[key]
                            
        if removals is not None:
            # identify elements to be remove in one loop, then remove them in separate loop
            # in case removal affects iteration
            tobeRemoved = []
            usedkeys = []
            for child in new_element.iterdescendants():
                for key in removals:
                    if key in child.tag :
                        tobeRemoved.append( child )
                        usedkeys.append(key)
                    if key in child.attrib:
                        if removals[key]==child.attrib[key]:
                            tobeRemoved.append( child )
                            usedkeys.append(key)
                for key in usedkeys:
                    if key in removals: del removals[key]
            for child in tobeRemoved:
                parent = child.getparent()
                parent.remove(child)
            
        if additions is not None:
            used_keys = []
            for child in new_element.iterdescendants():
                for key in additions:
                    if key not in used_keys:
                        if debug:
                            LL = len('ProcessXML.makeNewElement')
                            if debug: print 'ProcessXML.makeNewElement child',child,'\n',LL*' ','child.tag',child.tag,'\n',LL*' ','child.attrib',child.attrib,'\n',LL*' ','key',key,'\n',LL*' ','len(new_element)',len(new_element),'\n',LL*' ','used_keys',used_keys
                        if key in child.tag:
                            parent = child.getparent()
                            sE = etree.SubElement(parent, child.tag)
                            sE.text = additions[key]
                            if debug : print 'ProcessXML.makeNewElement key is in child.tag. parent',parent,'sE.text',sE.text
                            used_keys.append(key) # prevent infinite loop?
                        if key in child.attrib:
                            parent = child.getparent()
                            sE = etree.SubElement(parent, child.tag)
                            if debug : print 'ProcessXML.makeNewElement key is in child.attrib. parent',parent,'sE',sE
                            for k in child.attrib:
                                if k==key:
                                    sE.set(key,  additions[key])
                                else:
                                    sE.set(k, child.attrib[k])
                            used_keys.append(key)  # prevent infinite loop?
                    

        return   new_element

    def tellElement(self,element,words=None):
        '''
        print properties of element
        '''
        print '\n ProcessXML.tellElement:'
        if words is not None: print words,
        print element,'element',etree.tostring(element,pretty_print=True)
        if 0:
            for child in element.iterdescendants():
                print 'child tag',child.tag,'text',child.text,'tail',child.tail,'attrib',child.attrib



        return 
    def getFilesInDir(self,dir,suffix):
        '''
        get list of the full pathname of files in dir that end in suffix
        '''
        ds = dir + '/'
        return [ds+f for f in os.listdir(dir) if f.endswith(suffix)]
    def getOriginalXMLFile(self):
        return self.originalXML
    def getLatestXMLFile(self,allowCWD=False,debug=False):
        '''
        get latest file that ends in 'authors.xml'
        Search in all parallel directories but not the current directory
        Avoid directory paths ending in 'xlrd' and 'xlwt'
        '''

        cwd = os.getcwd()
        up = os.path.split(cwd)[0] + '/'
        if debug: print 'ProcessXML.getLatestXMLFile cwd',cwd,'allowCWD',allowCWD
        dirs = []
        for f in os.listdir(up):
            full = up+f
            if os.path.isdir(full):
                if full.endswith('xlrd'):
                    if debug: print 'ProcessXML.getLatestXMLFile skip',full
                elif full.endswith('xlwt'):
                    if debug: print 'ProcessXML.getLatestXMLFile skip',full
                else:
                    if allowCWD or full!=cwd: dirs.append(full)
        flist = []
        for d in dirs:
            if debug: print'ProcessXML.getLatestXMLFile searching',d
            flist.extend(self.getFilesInDir(d,'authors.xml'))
        tf = {}
        for f in flist:
            tf[os.path.getmtime(f)] = f
            if debug: print 'ProcessXML.getLatestXMLFile ',f,os.path.getmtime(f)
        key = sorted(tf)[-1]
        if debug: print 'ProcessXML.getLatestXMLFile Latest file is',tf[key]
        return tf[key]
    def parseExtraINSPIREIDs(self,fn='../extra_INSPIRE-IDS.txt'):
        '''
        parse text file with extra INSPIRE-IDs
        format of a line in text file:
        n) authorname (GivenName FamilyName) ID
        return dict IIDdict with key = authorname value = [GivenName, FamilyName, ID]
        '''
        debug = False
        f = open(fn)
        print 'ProcessXML.parseExtraINSPIREIDs Opened',fn
        IIDdict = {}
        for line in f:
            if line[0]!='#':
                S = line.split()
                IID = S[-1]
                i1 = line.find(')')
                i2 = line.find('(')
                i3 = line.rfind(')')
                authorname = line[i1+1:i2].strip()
                GNFN = line[i2+1:i3].strip()
                GivenName,FamilyName = '',''
                Given = True
                R = GNFN.split()
                for s in R:
                    if s==R[-1]:       Given = False
                    if s[0].islower(): Given = False
                    if Given: 
                        if len(GivenName)>0: GivenName += ' '
                        GivenName += s
                    else:
                        if len(FamilyName)>0: FamilyName += ' '
                        FamilyName += s
                if authorname in IIDdict:
                    print 'ProcessXML.parseExtraINSPIREIDs ERROR key',authorname,'already exists in IIDdict with value',IIDdic[authorname]
                    sys.exit('ProcessXML.parseExtraINSPIREIDs ERROR key '+authorname+' already exists')
                IIDdict[authorname] = [GivenName, FamilyName,IID]
                if debug:
                    print 'input line',line[:-1]
                    print 'authorname',authorname,'GivenName',GivenName,'FamilyName',FamilyName,'IID',IID
                else:
                    print authorname,IID
        f.close()
        return IIDdict
    def findINSPIREID(self,authorname):
        '''
        given authorname, try to return INSPIRE-ID
        '''
        if self.INSPIREIDs is None:
            self.INSPIREIDs = self.parseExtraINSPIREIDs()
        if authorname in self.INSPIREIDs:
            return self.INSPIREIDs[authorname][2]

        return None
if __name__ == '__main__' :
    fn = 'authors.xml'
    #fn = 'ForXMLDebug/example.minimal.xml'
    #filenames = ['ForXMLDebug/example.fulldata.xml','ForXMLDebug/example.group.xml','ForXMLDebug/example.minimal.xml','ForXMLDebug/example.multicollaboration.xml']
    sfn = 'ForXMLDebug/authors.xsd'
    print 'fn',fn
    
    PX = ProcessXML()
    #PX.setSchemaFile(sfn)
    PX.open(fn)

    if 0: # test parsing file with extra INSPIRE-IDs
        IIDdict = PX.parseExtraINSPIREIDs()
    
    if 0: # test validation
        for fn in filenames:
            PX.open(fn)
        
            valid = PX.schema.validate(PX.tree)
            print 'valid',valid
            #PX.schema.assertValid(PX.tree)

    if 0: # test getLatestXMLFile
        fn1 = PX.getLatestXMLFile()
        print 'latest xml file',fn1,'CWD not allowed'
        fn2 = PX.getLatestXMLFile(allowCWD=True)
        print 'latest xml file',fn2,'CWD ALLOWED'

    if 1: # test obtain xml for author
        al = [ 'D.E. Jaffe', 'M.V. Diwan', 'F.P. An']
        al = ['J. Dove', 'J. de Arcos']
#        apn = open('author-paper-name.txt')
#        for line in apn:
#            al.append(line[:-1])

        for a in al:
            pElement = PX.getPerson(a,debug=False)
            print a,pElement,PX.getPersonOrgID(pElement)
            PX.tellElement(pElement,'getPerson for '+a)
            IID = PX.findINSPIREID(a)
            print 'Found INSPIRE-ID',IID,'for',a
            #print etree.tostring( pElement )


    if 0: # test creating new xml entry for author
        a = 'Y.K. Heng'
        pElement = PX.getPerson(a)

        PX.tellElement(pElement,'original')
        replacements = {'authorNamePaper' : 'H.P. Fonebone',
                    'givenName'       : 'Henry P.',
                    'familyName'      : 'Fonebone',
                    'organizationid'  : 'o999',
                    'source'        : ['INSPIRE', 'INSPIRE-BR549']
                    }
        additions    = {'organizationid' : 'o345'}
        removals     = {'source'    : 'ORCID'}
        new_element = PX.cloneElement(pElement)
        new_element = PX.makeNewElement(new_element,replacements=replacements,additions=additions,removals=removals)
        PX.tellElement(new_element,'new from basis')

        PX.tellElement(pElement,'original again')




    if 0: # test obtain xml for institution   
        instDict = PX.getNC()

        debugI = False
        for i in instDict:
            iElement = None
            if 'altaff' not in instDict[i]:
                iElement = PX.getInst(PX.getAddressWords(instDict[i]),debug=debugI)
    #        if iElement is None:
    #            iElement = PX.getInst(i,debug=debugI)
            if iElement is None:
                print i,'NO MATCH'
            else:
                print i,iElement,PX.getOrgID(iElement),PX.getOrgName(iElement)
    #            print etree.tostring( iElement )
