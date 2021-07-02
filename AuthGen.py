#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
No arguments or "help" or "-help" or "--help" to get usage and a more detailed message.

Called as:

AuthGen <CollaboratorListFileName> [<StartDate as "YYYYMMDD">]
The file is an Excel file. <StartDate> defaults to todays date.

Generate TeX files for use as author lists in these formats (more may be added as needed):
1) PhysRev
2) Elsevier
3) CPC (add 20150611)
4) JCAP (add 20161019)
5) APJ (add 20191101) can use same input as PhysRev

Authors with "StartDate" after the specified <StartDate> will be excluded.
Authors with no "StartDate" are always included.

Expects an Excel file with columns as listed in __init__ .
If PublishName is blank, it tries to construct one, i.e. "William Steven James" becomes "W.S.~James".
  (In that case, a new excel file is produced, with "new_" prepended. It can be renamed to the old file and used in the
   future, but it will require the "StartDate" column to be manually formated for dates. It is also prefered to format
   the top row in bold, and to freeze the frame for the benefit of scrolling while keeping the column labels in view.)
If PublishName is not blank, it is used as-is.
This permits TeX special characters or a "non-derivable" name to be specified directly in the Excel file.

R. Hackenburg   24 Feb 2014.

ADDITIONAL IMPORTANT NOTES 20150501 D.JAFFE (20190127, 20200608 more notes)
1. Create dyb_collabotion_list.xls with twiki
2. open with excel
3. specify formats for dates columns as YMD : Use `Number` with Custom date
3A. Remove rows with 0000-00-00 as start date. Delete row of "Tomas Wise" from Yale.
3B. Fix Tadeas Dohnal and Martin Dvorak (Charles) to use ascii characters
3C. Remove row with 'NCTU	Lam	Thi To Uyen	touyenlamthi@gmail.com	2019-03-12	2019-09-30	former' (not on Daya Bay >1y)
3D. Remove 'BNL Zavadskyi ...' should be Dubna.
4. save as excel 95 .xls
5. then run AuthGen
This procedure is necessary to produce a file that can be processed by xlrd.

ADDITIONAL NOTES 20201214 FOR GENERATION OF CPC FILE WITH CHINESE NAMES
1. Include coding line as second line in this file (see above). Needed to read in html file.
2. Use ProcChiName.
3. Can set self.AddChineseNames with any non-blank input as 5th (from 1) argument
3. Note that automated pdf test will not work. Use Texshop by hand instead. 

SPECIAL NOTES FOR GENERATION OF AUTHORLIST OF DETECTOR PAPER 20150501 D.JAFFE
1.  Copy extra_authors_and_affiliations.txt from last used authorlist (../Osc8AD2014Paper/)
   Get latest used file
2.  mv extra_authors_and_affiliations.txt byhand_extra_authors_and_affiliations.txt
   Rename file for concatenation
3.  python PreGen.py
   Produce  legacy_authors_affiliations_pubNames.txt from  DYB_rate_prl.tex (first major publication)
4.  cat byhand_extra_authors_and_affiliations.txt legacy_authors_affiliations_pubNames.txt >extra_authors_and_affiliations.txt
   Concatenate to produce extra_authors_and_affiliations.txt needed by AuthGen
5.  python ../AuthGen.py dyb_collaboration_list_timestamp_20140601.xls 20140601
   Makes the author list. Note that only Elsevier.tex was carefully checked.

ADDITIONAL NOTES FOR DETECTOR PAPER AUTHORLIST 20150803 D.JAFFE
a. Steps 3,4,5 are repeated to produce new author list if changes made to 'byhand...'
b. Modify to allow 3d institution
b.1.  backup first....   cp AuthGen.py AuthGen.py.Before_Third_Institution

ADDITIONAL NOTES FOR ADD 'Now at....' 20160309 D.Jaffe
1. Elsevier.tex can be done by using \fntext as used for 'Deceased'
2. PhysRev.tex requires use of \altaffiliation
3. Testing of PhysRev.tex requires generation of a list of references because 'Now at...' as \altaffiliation appears only when the references are generated.
3.1 modification of AuthorList/test_PhysRev_authorlist.tex
3.2 addition of AuthorList/fake_PhysRev_refs.bib to svn
3.3 softlink of both of the above into the current working directory followed by 
3.4 pdflatex test_PhysRev_authorlist; bibtex test_PhysRev_authorlist ; pdflatex test_PhysRev_authorlist; pdflatex test_PhysRev_authorlist
4. For CPC.tex use \thanks, but this only works if there is a single 'Now at' institution


ADDITIONAL NOTES FOR JOINT MINOS-DYB AUTHORLIST 20160427 D.Jaffe
1. Usual command to generate DYB author list ( python ../AuthGen.py dyb_collabotion_list_20150707.xls 20150707 )
2. python merge.py
3. result is in test_combined_authorlist.pdf

ADDITIONAL NOTES FOR GENERATION OF TEXT FILE LISTING AUTHOR NAMES 20160607 D.Jaffe
1. Functionality added. Output file is author-paper-name.txt

ADDITIONAL NOTES FOR GENERATION OF XML FILE 20160616 D.Jaffe
1. xml file 'dyb_authors.xml' generated after .tex and .txt files have been written



'''
import sys
import os
import time
import string
import xlrd
import datetime
import ProcessXML
import ProcChiName


class Main():
    def __init__( self, FileName, DateString, debug=0, AddChineseNames=False ):

        self.debug = debug # higher numbers, more debuggin
        
        self.InstitutionCol  = 0
        self.FamilyNameCol =   1
        self.GivenNameCol =    2
        self.EmailCol =        3
        self.DateStartCol =    4
        self.DateEndCol =      5
        self.StatusCol =       6

        self.FamilyNameCol_ref  =  2
        self.GivenNameCol_ref   =  3
        self.PublishNameCol_ref =  4 # only valid for refSheet

        self.prefix = ''
        cwd = os.getcwd()
        lastsubdir = cwd.split('/')[-1]
        self.prefix = ''
        if lastsubdir!='Authorlist': self.prefix = '../'

        # 20201215 add Chinese names to CPC
        self.AddChineseNames = AddChineseNames
        charset='utf-8'#'gb2312'        
        if self.AddChineseNames:
            self.ProcChiName = ProcChiName.ProcChiName()
            hfn = self.prefix + 'http_dayabay.ihep.ac.cn_internal_contacts.php_20201214.html'
            self.ChineseNames = self.ProcChiName.Main(hfn=hfn,debug=self.debug)

        # the spreadsheet that has the correspondance between the family and given
        # names and the names to be used in the authorlist
        self.PubNameFileName = self.prefix + 'list_with_pubnames.xls'

        # file with address of each institution
        self.AddressListFileName = self.prefix + 'addresslist_for_Elsevier.tex'

        # output xml file
        self.output_xml = 'dyb_authors.xml'

        # need alphabetical superscripts for JCAP
        self.superAlpha = {}
        j = 0
        for w in ['','a']:
            for x in string.ascii_lowercase:
                j += 1
                self.superAlpha[j] = w+x
        

        # establish range of allowed dates
        if len(DateString)==8:
            year  = int(DateString[0:4])
            month = int(DateString[4:6])
            day   = int(DateString[6:8])
            dateSafe = (year, month, day, 0, 0, 0)
            print "Generating author lists for authors with start dates before", year,month,day,'dateSafe',dateSafe
        else:
            print "\n ERROR Date format not recognized [" + DateString + "], must be [YYYYMMDD] \n"
            return

        Success = True

        # open the spreadsheet produced by IB adminstrators webpage
        wb =  xlrd.open_workbook(FileName)
        self.WorkBook = wb

        # open the spreadsheet that has the correspondance between the family and given
        # names and the names to be used in the authorlist
        self.PubNameBook = xlrd.open_workbook(self.PubNameFileName)
        self.PubNameSheet = self.PubNameBook.sheet_by_index(0)

        Authors = {} # map of authornames and institution(s)
        AuthorList = [] # list of index names
        Rejects = {} # map of rejected index names

        sheet = wb.sheet_by_index(0)
        row = sheet.row(0)
        for Irow in range( 1,sheet.nrows ):
            Institution =  sheet.cell_value(Irow,self.InstitutionCol).replace(' ','') # remove blanks from institution names
            Institution2=  ''
            Institution3=  ''
            FamilyName =   sheet.cell_value(Irow,self.FamilyNameCol )
            GivenName =    sheet.cell_value(Irow,self.GivenNameCol  )
            Email =        sheet.cell_value(Irow,self.EmailCol      )
            Status =       sheet.cell_value(Irow,self.StatusCol     )
            Days =         sheet.cell_value(Irow,self.DateStartCol  )
            PublishName = None
            OK = self.acceptableDate(dateSafe, Irow, sheet)
            if self.debug>1: print FamilyName,GivenName,Status,dateSafe, xlrd.xldate_as_tuple(Days,self.WorkBook.datemode), OK
            if OK :
                PublishName = self.GetPubName(FamilyName,GivenName)
                if PublishName is None:
                    print 'NO PUBLICATION NAME FOR FamilyName',FamilyName,'GivenName',GivenName,'of',Institution,\
                          '. Edit',self.PubNameFileName,'to add this name'
                    Success = False
            else:
                if self.debug>1: print FamilyName,GivenName,Status,'dateSafe',dateSafe, 'REJECTED by status and/or date'
                IndexName = str(FamilyName + ' ' + GivenName)
                Rejects[IndexName] = [ PublishName, str(Institution), str(Institution2), str(Institution3) ]
                



            # create key = IndexName for map to authorname and institutions
            # also store all keys in list for alphabetic sorting
            if OK: 
                IndexName = str(FamilyName + ' ' + GivenName)
                if IndexName in Authors:
                    if Institution in Authors[IndexName][1:]:
                        print IndexName,'is already in authorlist as',IndexName,Authors[IndexName],', so do not add it again'
                    else:
                        i = Authors[IndexName].index('')
                        Authors[IndexName][i] = Institution

                else:
                    Authors[IndexName] = [ str(PublishName), str(Institution), str(Institution2), str(Institution3) ]
                    AuthorList.append( IndexName )


        # optionally add extra authors and affiliations. This is also an opportunity to fix mistakes
        # in the input excel file
        self.addAuthorsAndAffiliations(Authors, AuthorList)

        # see how many rejects were actually accepted because of duplicate entries
        RejectList = []
        once = False
        for IndexName in Rejects:
            if IndexName in Authors:
                print 'Rejection of',IndexName,'of',Authors[IndexName][1],'with Publication Name',Authors[IndexName][0],'over-turned due to accepted duplicate'
                once = True
            else:
                RejectList.append(IndexName)
        if once : print ' '
        if self.debug>0: 
            for IndexName in RejectList:
                print IndexName,'of',Rejects[IndexName][1],'REJECTED'

        # remove authors with no affiliation. 20160629 and remove authors with no publication name
        Removals = []
        for IndexName in Authors:
            remove = len(Authors[IndexName][1])==0 and len(Authors[IndexName][2])==0 and len(Authors[IndexName][3])==0
            remove = remove or (Authors[IndexName][0] is None)
            if remove: Removals.append(IndexName)
            
        for IndexName in Removals:
            print 'Remove',IndexName,'with Publication Name',Authors[IndexName][0],'because s/he has no affiliation or Publication Name'
            AuthorList.remove(IndexName)
            del Authors[IndexName]

        # alphabetize authorlist by IndexName
        AuthorList.sort(key=lambda v: v.lower())

        # 20170920 also create alphabetized list using publication name to handle L.Whitehead -> L.W.Koerner
        SortedPubNames = self.SortByPublicationName(Authors)
        if self.debug>2:
            print '\n ------------------- AuthorList SortedPubNames before replacement'
            for A,B in zip(AuthorList,SortedPubNames):
                print A,B
        # 20170920 replace AuthorList alphabetized by IndexName to AuthorList alphabetized by publication names
        AuthorList = self.ReplaceAuthorList(AuthorList,SortedPubNames)
        if self.debug>2: 
            print '\n ------------------- AuthorList SortedPubNames after replacement'
            for A,B in zip(AuthorList,SortedPubNames):
                print A,B


        
        if self.debug>1:
            print '{0:30} {1:20} {2:20} {3:20} {4:20}'.format('IndexName','PublicationName','Institution1','Institution2','Institution3')
            for IndexName in AuthorList:
                a = Authors[IndexName]
                print '{0:30} {1:20} {2:20} {3:20} {4:20}'.format(IndexName,a[0],a[1],a[2],a[3])

        # finished processing input. Now make the author lists
        # physrev list is easy since institutions are automatically alphabetized
        # elsevier requires some extra processing to produce \def{XX}N and
        defList = []
        for IndexName in AuthorList:
            for i in [1, 2, 3]:
                Institution = str( Authors[IndexName][i] )
                if Institution!='' and Institution not in defList:
                    #print 'IndexName',IndexName,'i',i,'Institution',Institution
                    defList.append(Institution)
        if self.debug>1:
            print '\nInstitutions:',
            for Inst in defList: print Inst,
            print "\n"
            

        # open the files that will contain the author lists
        fp = open("PhysRev.tex","wb")
        fe = open("Elsevier.tex","wb")
        fc = open("CPC.tex","wb")
        fj = open("JCAP.tex","wb")
        fx = open("EJPC.tex","wb")
        ft = open("author-paper-name.txt","wb") 
        journalNames = [ fp.name.replace('.tex',''), fe.name.replace('.tex',''), fc.name.replace('.tex',''), fj.name.replace('.tex',''), fx.name.replace('.tex',''), 'APJ' ] # APJ can use same file as PhysRev

        # pre-pend generator information for each output file
        los = self.getGenInfo()
        for a in los:
            a = '%%% ' + a + '\n'
            fp.write(a)
            fe.write(a)
            fc.write(a)
            fj.write(a)
            fx.write(a)

        # for elsevier and JCAP, must preface authorlist with list of institutions and reference numbers
        self.writeDefList(fe, defList)
        self.writeDefList(fj, defList,JCAP=True)
        # for CPC, preface author list with newcommands for each institution with reference number
        self.writeCPCInstList(fc, defList)
        # for physrev, use address list to generate newcommands for each institution
        self.writeNewCommand(fp, defList)
        # 20210408 make sure \author starts on new line for PhysRev
        fp.write('\n') 
        # for EJPC, structure is
        # \author{
        #          A1\thanksref{I1} \and A2\thanksref{I1,NOTE1} \and A3\thanksref{I2,I3}
        #        }
        # \thankstext{NOTE1}{Now at xxx}
        # \institute{
        #              Institute1\label{I1} \and \Institute2\label{I2} \and \Institute3\label{I3} 
        #           }
        fx.write('\\author{\n') #remember to close this
        
        # now generate the author listings in the file
        # First add 'Deceased.' footnote. At present this only works for Elsevier.
        # For PhysRev, if \altaffilation is used, it must appear first in list of affiliations. In the present state,
        # 'Deceased.' will not appear, but latex will not halt during processing.
        
        NoneDead = True
        for IndexName in AuthorList:
            P,I,I2,I3 = Authors[IndexName]
            if I2=='DEAD' or I3=='DEAD': NoneDead = False
        if not NoneDead:
            fe.write('\\fntext[DEAD]{Deceased.}\n')
            fj.write('\\note[DEAD]{Deceased.}\n')
            fp.write('\\newcommand{\\DEAD}{\\altaffiliation[]{Deceased.}}\n')
            fx.write('\\thankstext{\\DEAD}{Deceased.}\n')

        # now go author by author adding institutional affiliations
        # use of 'Now at' works for PhysRev and Elsevier for an arbitrary of additional institutions, but
        # for CPC it only works for a single 'Now at'

        fxNowAtLines = ''
        countNowAt = 0
        for k,IndexName in enumerate(AuthorList):
            PublishName, I1, I2, I3 = Authors[IndexName]
            Institution, Institution2, Institution3 = I1.replace('NOWAT_',''), I2.replace('NOWAT_',''), I3.replace('NOWAT_','')
            if self.AddChineseNames : ChineseName = self.ProcChiName.bestMatch(IndexName,self.ChineseNames,[Institution, Institution2, Institution3], debug=self.debug)

            # text version of publication name
            ft.write(self.makeTextName(PublishName) + '\n')

            # for PhysRev \altaffiliation is used for 'Now at' and must appear first in list of affiliations

            alt = []
            reg = []
            for x in Authors[IndexName][1:]:
                if 'NOWAT' in x:
                    countNowAt += 1
                    alt.append( x.replace('NOWAT_','') )
                else:
                    if x!='': reg.append( x )
            physRevInsts = []
            physRevInsts.extend(alt)
            physRevInsts.extend(reg)
                                                 
            #########print 'PublishName, Institution, Institution2 ',PublishName, Institution, Institution2
            if (Institution is None) or (PublishName is None):
                ii = AuthorList.index(IndexName)
                print 'AuthGen: ERROR IndexName',IndexName,'ii',ii,'AuthorList[ii]',AuthorList[ii],\
                      'Institution',Institution,'PublishName',PublishName
            feLine = "\\author[\\"+Institution
            fjLine = "\\author[\\"+Institution

            fpLine = "\\author{" + PublishName + "}"
            for x in physRevInsts:
                fpLine += "\\"+x
            fcLine = ''
            fxLine = PublishName + '\\thanksref{'+Institution
            if k==0: fcLine = "\\author{\n " # prefix for CPC
            cName = ''
            if self.AddChineseNames and ChineseName is not None :

                try: cName = '(' + ChineseName + ')'
                except UnicodeDecodeError:
                    if debug>1 : print 'AuthGen: cName failed assignment for ChineseName',ChineseName
                    try: cName = '(' + ChineseName.encode(charset) + ')'
                    except UnicodeDecodeError:
                        if debug>1 : print 'AuthGen: cName failed 1st encode for ChineseName',ChineseName
                        try: cName = '(' + ChineseName.encode(charset,'ignore') + ')'
                        except UnicodeDecodeError:
                            print 'AuthGen: ERROR Could not use ChineseName',ChineseName
                            cName = ''
                if debug>1 : print 'AuthGen: before adding to PublishName, cName',cName,'type(cName),type(fcLine)',type(cName),type(fcLine)
                Institution  = Institution.encode(charset)
                Institution2 = Institution2.encode(charset)
            fcLine += PublishName 
            try: fcLine += cName
            except UnicodeDecodeError:
                fcLine += cName.decode(charset)
            fcLine += "$^{\\" + Institution
            if self.AddChineseNames and debug>0 : print 'AuthGen: before appending Institution2, fcLine',fcLine
            if len(Institution2)>0:
                if Institution2!='DEAD':
                    fjLine += ",\\"+Institution2
                    if 'NOWAT' not in I2:
                        feLine += ",\\"+Institution2
                        fcLine += ",\\"+Institution2
                        fxLine += ","+Institution2
            if len(Institution3)>0:
                if Institution3!='DEAD':
                    fjLine += ",\\"+Institution3
                    if 'NOWAT' not in I3:
                        feLine += ",\\"+Institution3
                        fcLine += ",\\"+Institution3
                        fxLine += ","+Institution3
            feLine += "]{"+PublishName
            fjLine += "]{"+PublishName
            if Institution2=='DEAD':
                feLine += "\\fnref{DEAD}"
                fjLine += "\\note{DEAD}"
                fxLine += ',DEAD'
            if 'NOWAT' in I2:
                feLine += '\\fnref{'+Institution2+'}'
                fjLine += '\\'+Institution2+'note'
                x = self.getAddressForInst(Institution2)
                fcLine += '\\thanks{Now at: ' + x + '}'
                fxLine += ','+Institution2
                fxNowAtLines += '\\thankstext{'+Institution2+'}{Now at: ' + x + '}\n'
            if 'NOWAT' in I3:
                feLine += '\\fnref{'+Institution3+'}'
                fjLine += '\\'+Institution3+'note'
                x = self.getAddressForInst(Institution3)
                fcLine += '\\thanks{Now at: ' + x + '}'
                fxLine += ','+Institution3
                fxNowAtLines += '\\thankstext{'+Institution3+'}{Now at: ' + x + '}\n'
            feLine += "}"
            fjLine += "}"
            fxLine += '}'
            if k<len(AuthorList)-1:fxLine+= '\\and'
            fxLine += '\n'
#            if IndexName!=AuthorList[-1] : feLine +=","
            fcLine += "}$ \\and"
            feLine += "\n"
            fpLine += "\n"
            fcLine += "\n"
            fjLine += "\n"
            fe.write(feLine)
            fp.write(fpLine)
            if debug>0 and self.AddChineseNames : print 'AuthGen: before write, fcLine',fcLine
            try: fc.write(fcLine)
            except UnicodeEncodeError:
                fc.write(fcLine.encode(charset))
            fj.write(fjLine)
            fx.write(fxLine)

        fc.write("}\n") # termnination for \author prefix for CPC
        fx.write('}\n') #closes \author{

        ## add Now at for EJPC if needed
        if fxNowAtLines!='': fx.write(fxNowAtLines)

        ## EJPC format appears too stupid to be able to break many institutional addresses on more than one page,
        ## so just do this to make the test file look better
        ##fx.write('\\clearpage\\vfill\\eject %%%%% COSMETIC\n')

        ## now add addresses of institutions to elsevier list
        self.writeElsevierAddresses(fe, defList)

        ## add addresses  of institution for EJPC
        self.writeElsevierAddresses(fx, defList, EJPC=True)

        ## now add address of institution to JCAP list
        self.writeJCAPAddresses(fj, defList)

        ## now add address and other stuff to CPC file
        self.writeCPCAddresses(fc, defList)
        
        fp.close()
        fe.close()
        fc.close()
        fj.close()
        ft.close()
        fx.close()

        # APJ uses same input file as PhysRev
        from shutil import copyfile
        copyfile( fp.name, 'APJ.tex')

        # 20201222 Report success (or failure), authorlists and authorlists to be tested.
        # No CPC test if Chinese names have been added. That has to be done separately.
        if Success:
            words = '\nSuccessfully generated authorlists'
            jNames = []
            for name in journalNames:
                words += ' ' + name
                if self.AddChineseNames and name=='CPC':
                    continue
                else:
                    jNames.append(name)
            words += ' ' + ft.name
            words += '\n'
            print words
            print 'Can now test authorlists for',' '.join(jNames)
            if 'CPC' in words and countNowAt>1: print '+++ WARNING +++ `Now at:` used',countNowAt,\
                'Only a single `Now at` institutions is enabled for CPC'
            
            ### test the authorlists
            self.testAuthorList( jNames)
        else:
            sys.exit('\n*** FAILURE: Check text above for instructions and messages ****\n')
            

        ### generation of xml file
        self.PX = ProcessXML.ProcessXML()
        original = True
        if original: 
            protoXML = self.PX.getOriginalXMLFile()
        else:
            protoXML = self.PX.getLatestXMLFile()
        self.makeXMLFile(authors=Authors,protoXML=protoXML)
        return
    def SortByPublicationName(self,Authors):
        '''
        20170920
        return list SBPN where each element is list with first element PubNameWithLastNameFirst, second element IndexName
        '''
        SBPN = []
        for IndexName in Authors:
            PubName = Authors[IndexName][0]
            pns = PubName.split('~')
            last = pns[-1]
            pns.remove(last)
            pns.insert(0,last)
            PubNameWithLastNameFirst = ' '.join(pns)
            SBPN.append( [PubNameWithLastNameFirst,IndexName] )
        SortedPubNames = sorted(SBPN,key=lambda x:x[0])
        return SortedPubNames
    def ReplaceAuthorList(self,AuthorList,SortedPubNames):
        '''
        20170920
        return list of authors sorted by publication name rather than by IndexName
        check that all IndexNames in new list appear in original
        '''
        Problem = False
        newAL = []
        for pair in SortedPubNames: newAL.append( pair[1] )
        for IN in newAL:
            if IN not in AuthorList:
                print 'AuthGen.ReplaceAuthorList: IndexName',IN,'in new AuthorList does not appear in old AuthorList'
                Problem = True
        for IN in AuthorList:
            if IN not in newAL:
                print 'AuthGen.ReplaceAuthorList: IndexName',IN,'in old AuthorList does not appear in new authorList'
                Problem = True
        if Problem: sys.exit('AuthGen.ReplaceAuthorList There is a problem')
        return newAL
    def makeXMLFile(self,authors=None,protoXML='authors.xml'):
        '''
        generate xml file using authors dict and prototype xml file
        authors[IndexName] = [PublicationName, Inst1, Inst2, Inst3] = list of strings
        IndexName = familyname + ' ' + givenname
        PublicationName = author's name in latex format
        Inst1 = Abbreviation for institution1 for affiliation
        Inst2, Inst3 = idem for 2d, 3d institution affiliation, otherwise null string ''

        First establish map between authors key and values in xml for institutions including organization id number
        for each institution. The org. id number is needed to disambiguate authors with identical publication names. 
        '''
        print '\n',''.join(['_' for x in range(100)])
        print ''.join([' ' for x in range(25)]),'AuthGen.makeXMLFile Produce XML file for authors',''.join([' ' for x in range(25)]),
        print '\n',''.join(['_' for x in range(100)])
        
        
        if authors is None : sys.exit('AuthGen.makeXMLFile FAILURE No input authors')

        enableDebug = True  # set false to disable all debug output
            
        PX = self.PX
        PX.open(protoXML)

        debug = self.debug>0 and enableDebug
        
        Organizations = {} # key=Inst, value=xml element
        OrgIDs        = {} # key=Inst, value=organization id number
        sDIgrO        = {} # key=organization id number, key=Inst
        textNames     = {} # key=IndexName, value=text version of PublicationName (only periods and dashes allowed)
        orgsForName   = {} # key=IndexName, value= list of organization ids
        Persons       = {} # key=IndexName, value=xml element
#        debug = False and enableDebug
        bigDebug = self.debug>1 and enableDebug
        for IndexName in sorted(authors):
            if bigDebug: print IndexName,authors[IndexName]
            if IndexName in textNames:
                print 'AuthGen.makeXMLFile Duplicate IndexName',IndexName,'with textName',textNames[IndexName]
            else:
                textNames[IndexName] = self.makeTextName(authors[IndexName][0])
                orgsForName[IndexName] = []
            for instRaw in authors[IndexName][1:]:
                if instRaw!='':
                    inst = instRaw.replace('NOWAT_','')
                    Address = self.getAddressForInst(inst)
                    aWords = PX.getAddressWords(Address)
                    if inst not in Organizations:
                        if debug: print '  ',inst,Address,aWords
                        if inst=='Siena':
                            element = PX.getInst(inst,debug=debug)
                        else:
                            element = PX.getInst(aWords,debug=debug)
                        if element is not None:
                            Organizations[inst] = element
                            OrgIDs[inst] = PX.getOrgID(element)
                            if debug: print inst,'assigned org id',OrgIDs[inst],'org name',PX.getOrgName(element)
                        else:
                            sys.exit('AuthGen.makeXMLFile FAILURE No organization for '+inst+' '+Address)
        print 'AuthGen.makeXMLFile Successfully found xml element for',len(Organizations),'institutions'
        
        # create new organizations
        makeBronx = True
        for inst in Organizations:
            if 'Bronx' in PX.getOrgName(Organizations[inst]): makeBronx = False
        if makeBronx:
            debug = False
            inst = 'BCC' # gonna fix this one
            lastOrgID = sorted(OrgIDs.values(), key=lambda s: int(s[1:]))[-1]
            newOrgID = lastOrgID[0] +str( int(lastOrgID[1:])+1 )
            if newOrgID in OrgIDs.values(): sys.exit('AuthGen.makeXMLFile ERROR New org id ' + newOrdID + ' already a valid org id')
            if debug: print 'lastOrgID',lastOrgID,'newOrgID',newOrgID
            newOrg = PX.cloneElement(Organizations[inst])
            if debug: PX.tellElement(newOrg,'original')
            address = self.getAddressForInst(inst)
            replacements = { 'id' : newOrgID,
                            'orgAddress' : address, 
                             'orgStatus'  : 'nonmember',
                             '{'+PX.ns['foaf']+'}'+'name'       : address, 
                             'orgName'    : 'Bronx Community College'}
            newOrg = PX.makeNewElement(newOrg,replacements=replacements)
            if inst in Organizations: print 'AuthGen.makeXMLFile For inst',inst,'replace',PX.getOrgName(Organizations[inst]),'with',PX.getOrgName(newOrg)
            Organizations[inst] = newOrg
            OrgIDs[inst] = newOrgID
            if debug: PX.tellElement(newOrg,'fixed')
            print 'AuthGen.makeXMLFile Created new xml for organization',inst,'org id',OrgIDs[inst]

        # add attribute 'source'='INSPIRE' to cal:orgName
        for inst in Organizations:
            element = Organizations[inst]
            if bigDebug: print 'inst',inst
            for child in element.iterdescendants():
                if 'orgName' in child.tag:
                    child.set('source','INSPIRE')
                if bigDebug: print 'tag',child.tag,'attrib',child.attrib,'tail',child.tail,'text',child.text
            
        # reverse map of OrgIDs
        for inst in OrgIDs:
            sDIgrO[OrgIDs[inst]] = inst
            if debug: print 'AuthGen.makeXMLFile Inst',inst,'org id',OrgIDs[inst]

        for oid in sorted(sDIgrO, key=lambda s: int(s[1:])):
            inst = sDIgrO[oid]
            if debug: print 'AuthGen.makeXMLFile org id',oid,'inst',inst
            
        # now populate orgsForName
        for IndexName in sorted(authors):
            for instRaw in authors[IndexName][1:]:
                if instRaw!='':
                    inst = instRaw.replace('NOWAT_','')
                    oid = OrgIDs[inst]
                    orgsForName[IndexName].append(oid)

        # error checking and debugging
        debug = self.debug>1 and enableDebug
        if debug:
            for inst in sorted(Organizations): print inst,OrgIDs[inst],PX.tostring(Organizations[inst])
        debug = False and enableDebug
        for IndexName in textNames:
            if debug: print IndexName,textNames[IndexName],orgsForName[IndexName]
            if len(orgsForName[IndexName])==0: sys.exit('AuthGen.makeXMLFile ERROR No org id for '+IndexName)

        # xml element to used as template for authors without xml element
        elementJaffe = None
        for IndexName in authors:
            if 'Jaffe' in IndexName:
                elementJaffe = PX.getPerson(textNames[IndexName])
                if debug: PX.tellElement(elementJaffe,'elementJaffe')
                break
                
                
        # now get xml element for each author
        # First try to get element for author using known organizations of author to disambiguate,
        # for author without element, search for by name only and add known organizations,
        # if that search is unsuccessful, create a new xml element. 
        # Then make sure author is only affiliated with known organizations.
        debug = self.debug>1  and enableDebug
        for IndexName in authors:
            if debug : print 'AuthGen.makeXMLFile try to get xml element for author with IndexName',IndexName
            element = PX.getPerson(textNames[IndexName],orgs=orgsForName[IndexName],debug=debug)
            if element is None:
                if debug: 
                    words = ''
                    for o in orgsForName[IndexName]: words = o+'-'+sDIgrO[o]+' '
                    print 'AuthGen.makeXMLFile No xml for',IndexName,'with Insts,OrgIds',words
                    e2 = PX.getPerson(textNames[IndexName],orgs=orgsForName[IndexName],debug=True)
                people = PX.getPeople(textNames[IndexName],orgs=None,debug=False)
                if debug : print 'AuthGen.makeXMLFile people=',people
                if len(people)==1:
                    if debug: 
                        print 'AuthGen.makeXMLFile Found',len(people),'xml elements for',IndexName,'independent of organizations'
                        for person in people: PX.tellElement(person,words=str(people.index(person))+'th person')
                    element = people[0]
                    if debug: PX.tellElement(element,'original, before fix')
                    for o in orgsForName[IndexName]: 
                        element = PX.makeNewElement(element,replacements={'organizationid':o})
                    if debug: PX.tellElement(element,'fixed?')
                    print 'AuthGen.makeXMLFile Successfully found xml for author',IndexName
                elif len(people)==0:
                    element = self.makeXMLPerson(elementJaffe, IndexName, textNames[IndexName], orgsForName[IndexName], debug=debug )
                    print 'AuthGen.makeXMLFile Generated new xml for author',IndexName
                else:
                    sys.exit('AuthGen.makeXMLFile FAILURE Could not get xml for Person '+IndexName)
            ElOids = PX.getPersonOrgID( element )
            knownOids = orgsForName[IndexName]
            if debug : print 'AuthGen.makeXMLFile ElOids',ElOids
            if debug : print 'AuthGen.makeXMLFile knownOids',knownOids
            if set(ElOids)!=set(knownOids):
                if debug: PX.tellElement(element,'before fixing organizations')
                for o in knownOids:
                    if o not in ElOids: element = PX.makeNewElement(element,additions={'organizationid':o},debug=debug)
                for o in ElOids:
                    if o not in knownOids: element = PX.makeNewElement(element,removals={'organizationid':o},debug=debug)
                if debug: PX.tellElement(element,'after fixing organizations')
                print 'AuthGen.makeXMLFile Successfully corrected organizations in xml for author',IndexName
            if set(PX.getPersonOrgID(element))!=set(orgsForName[IndexName]):
                print 'AuthGen.makeXMLFile FAILURE to correct organizations for IndexName',IndexName,'with known orgs',orgsForName[IndexName]
                PX.tellElement(element,'FAILURE to correct organizations')
                sys.exit('AuthGen.makeXMLFile FAILURE to correct organizations')
            aids = PX.getPersonAuthorID(element)
            if len(aids)==0: print 'AuthGen.makeXMLFile WARNING No author identifier for',IndexName


                
            Persons[IndexName] = element

        # add authorids if needed
        Persons = self.addAuthorID(Persons)
        
        # ready to make new authors element tree
        # create header
        AET = self.makeXMLHeader(PX)

        # now add organizations and authors
        # organizations listed by organization id
        # authors alphabetically by last name
        debug = False and enableDebug
        sO = PX.etree.SubElement(AET, PX.etree.QName(PX.CAL_NS,'organizations'))
        for oid in sorted(sDIgrO, key=lambda s: int(s[1:])):
            inst = sDIgrO[oid]
            sO.append( Organizations[inst] )
            if debug : print 'AuthGen.makeXMLFile Appended inst',inst,'org id',oid,'org name',PX.getOrgName( Organizations[inst] )
        sA = PX.etree.SubElement(AET, PX.etree.QName(PX.CAL_NS,'authors'))
        for IndexName in sorted(Persons):
            sA.append( Persons[IndexName] )
                                 
        debug = False and enableDebug
        if debug: PX.tellElement(AET,'new authors element tree')

            
        tree = PX.etree.ElementTree(element=AET)
        tree.write(self.output_xml,pretty_print=True)
        # prepend the xml version taken from the original file
        p1 = open(protoXML,'r')
        firstLine = p1.readline()
        p1.close()

        p2 = open(self.output_xml,'r')
        p2all = p2.read()
        p2.close()

        p2 = open(self.output_xml,'w')
        p2.write(firstLine)
        p2.write(p2all)
        p2.close()
        
        print 'AuthGen.makeXMLFile Wrote xml to ',self.output_xml
        
        return
    def addAuthorID(self,Persons,debug=False):
        '''
        add authorid to appropriate Persons dict of elements if available and needed
        byHandDict entries supplied by Ruirong Liu liurr@ihep.ac.cn 20161020 email
        INSPIRE id is 'INSPIRE-NNNN', ORCID id is 'NNN'
        '''
        byHandDict = {'Sam Kohn' : ['INSPIRE-00526971'],
                        'Jason Dove' : ['INSPIRE-00625864'],
                        'Zhaokan Cheng' : ['INSPIRE-00625792'],
                    'Yuhang Guo' : ['INSPIRE-00561910','ORCID: 0000-0002-9631-587X'],
                    'Jenny H.C. Lee' : ['INSPIRE-00625804'],
                    'Yu-Cheng Lin' : ['INSPIRE-00626068'],
                    'Wenjie Wu' : ['INSPIRE-00625856','ORCID: 0000-0003-4379-9548'],
                    'Haibo Yang' : ['INSPIRE-00625810'],
                    'Ziping Ye' : ['INSPIRE-00625788'],
                    'Konstantin Treskov' : ['INSPIRE-00626074'],
                    'Donald Jones' : ['INSPIRE-00637439']
                    }
        # search for exact matches to authors in byHandDict among input dict of xml elements for persons
        keyMatches = {}
        exactMatchDict = {}
        for IndexName in Persons:
            element = Persons[IndexName]
            authorname = self.PX.getAuthorName(element)
            givenname = self.PX.getGivenName(element)
            familyname = self.PX.getFamilyName(element)
            if authorname is None or givenname is None or familyname is None:
                self.PX.tellElement(element,'AuthGen.addAuthorID ERROR No authorNamePaper or givenName or familyName?')
                sys.exit('AuthGen.addAuthorID ERROR No authorNamePaper or givenName or familyName?')
            keyMatches[IndexName] = []
            for key in byHandDict:
                lastName = key.split(' ')[-1]
                firstName= key.replace(lastName,'').strip()
                lastName = lastName.strip()
                if familyname==lastName:
                    if givenname==firstName: # definite match
                        keyMatches[IndexName].append(key)
                        if key in exactMatchDict:
                            print 'AuthGen.addAuthorID ERROR exact match already exists for',key
                            sys.exit('AuthGen.addAuthorID ERROR Duplicate exact match')
                        exactMatchDict[key] = IndexName
                        break
                    else:
                        keyMatches[IndexName].append(key)

        # process exact matches
        # Take no action if an xml element for authorid already exists with text for the numerical id
        # If an xml element exists for an authorid but without text, then add the numerical id
        # If an xml element does not exist for an authorid, create it and add the numerical id
        print 'AuthGen.addAuthorID process',len(exactMatchDict),'exact matches to add INSPIRE/ORCID numerical id'
        for key in exactMatchDict:
            IndexName = exactMatchDict[key]
            element = Persons[IndexName]
            aIDs = self.PX.getAuthorIDsElement(element)
            if aIDs is None:
                aIDs = self.PX.etree.SubElement(element,self.PX.etree.QName(self.PX.CAL_NS,'authorids'))
            for x in byHandDict[key]:
                if 'INSPIRE' in x:
                    el = self.PX.foundPersonAuthorID(element,'INSPIRE')
                    if el is None:
                        el = self.PX.etree.SubElement(aIDs,self.PX.etree.QName(self.PX.CAL_NS,'authorid'),source='INSPIRE')
                        if debug: print 'AuthGen.addAuthorID add element for INSPIRE authorid for',IndexName
                    if debug: print 'AuthGen.addAuthorID text for INSPIRE authorid is',el.text
                    if el.text is None or el.text=='': el.text = x
                if 'ORCID'   in x:
                    el = self.PX.foundPersonAuthorID(element,'ORCID')
                    if el is None:
                        el = self.PX.etree.SubElement(aIDs,self.PX.etree.QName(self.PX.CAL_NS,'authorid'),source='ORCID')
                        if debug: print 'AuthGen.addAuthorID add element for ORCID authorid for',IndexName
                    if debug: print 'AuthGen.addAuthorID text for ORCID authorid is',el.text
                    if el.text is None or el.text=='': el.text = x.replace('ORCID: ','')
            if debug : self.PX.tellElement(element,'AuthGen.addAuthorID results for IndexName='+IndexName)
            ######## remove element from dict to avoid duplication !!!!!!!!!!!!
            del byHandDict[key]

        # Report any remaining potential matches
        if len(byHandDict)>0:
            print 'AuthGen.addAuthorID remaining',len(byHandDict),'unmatched authors in byHandDict',byHandDict
        return Persons
    def makeXMLPerson(self,element, IndexName, PubName, OrgIDs, debug=False):
        '''
        return an xml element for author given by IndexName, text version of Publication Name and organization IDs (OrgIDs)
        given a valid xml element
        '''
        oid = OrgIDs[0]
        new_element = self.PX.cloneElement(element)
        family = IndexName.replace(IndexName.split(' ')[-1],'')
        given = IndexName.replace(family,'')
        j = PubName.rfind('~')
        aName = PubName
        if j>-1: aName = PubName[:j] + ' ' + PubName[j+1:]
        replacements = {'authorNamePaper' : aName,
                    'givenName'       : given,
                    'familyName'      : family,
                    'organizationid'  : oid,
                    'source'        : ['INSPIRE', '']
                    }
        if debug :
            print 'AuthGen.makeXMLPerson IndexName',IndexName,'PubName',PubName,'OrgIDs',OrgIDs
            print 'AuthGen.makeXMLPerson replacements',replacements
        new_element = self.PX.makeNewElement(new_element,replacements=replacements)
        if debug : self.PX.tellElement(new_element,'fixed with makeXMLPerson')
        return new_element

    def makeXMLHeader(self,PX):
        '''
        return top-most element of xml populated with the basic header information
        '''
        AET = PX.etree.Element('collaborationauthorlist',nsmap=PX.ns)
        sT  = PX.etree.SubElement(AET,PX.etree.QName(PX.CAL_NS,'creationDate'))
        sT.text = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M')
        spR = PX.etree.SubElement(AET,PX.etree.QName(PX.CAL_NS,'publicationReference'))
        spR.text = 'http://arXiv.org/abs/xxxPUT_IN_ARXIV_NUMBER_HERE'
        sCs  = PX.etree.SubElement(AET,PX.etree.QName(PX.CAL_NS,'collaborations'))
        sC   = PX.etree.SubElement(sCs,PX.etree.QName(PX.CAL_NS,'collaboration'),id='c1')
        sDB  = PX.etree.SubElement(sC, PX.etree.QName(PX.FOAF_NS,'name'))
        sDB.text = 'Daya Bay Collaboration'
        sEN  = PX.etree.SubElement(sC, PX.etree.QName(PX.CAL_NS,'experimentNumber'))
        sEN.text = 'DAYA-BAY'
        return AET
    def makeTextName(self,PublishName):
        '''
        return text name given publication name
        this is useful for making text file of author list
        '''
        l = PublishName.rfind('~')
        TextName = PublishName[:l] + ' ' + PublishName[l+1:]
        TextName = TextName.replace('~','')
        return TextName
    def getGenInfo(self):
        '''
        return list of strings with the date and time, current working directory
        and commands used for running AuthGen.py
        '''
        hdr = 'Generation information for this file'
        now = '20140529 09:01:16'
        now = datetime.datetime.now().ctime()
        cwd = os.getcwd()
        args= ''
        for a in sys.argv:
            args += a + ' '
        los = [hdr, now, cwd, args]
        #for a in los: print a
        return los
    def addAuthorsAndAffiliations(self, Authors, AuthorList):
        '''
        read a local text file that has authors and affiliations.
        this file can  be used to add an author or add an affiliation to a current author
        20150501 Local file can also hold PublicationName (i.e. "H.~P.~Fonebone" for Fonebone, Henry); however,
                 if PublicationName is already available in GetPubName, then that value will be used
        20160311 Add NOW AT processing
        20181224 Add SWAP action
        '''
        filename = 'extra_authors_and_affiliations.txt'
        if os.path.isfile(filename):
            print '\nUsing ' + filename + ' to add authors and/or affiliations\n'
            f = open(filename,'r')
            for line in f:
                # if line is not a comment, then parse it
                KeepGoing = True
                if line[0]!='#': #
                    splitline = line.split()
                    PubName = None
                    if len(splitline)==4:
                        Action, FamilyName, GivenName, Inst = splitline
                    elif len(splitline)==5:
                        Action, FamilyName, GivenName, Inst, PubName = splitline
                        if self.DuplicatePubName( PubName ):
                            for iN in Authors:
                                if Authors[iN][0]==PubName: KeepGoing = False
                            if self.debug>0: print 'addAuthorsAndAffiliations: PubName',PubName,'already specified for',FamilyName,GivenName,'KeepGoing',KeepGoing
                            if KeepGoing: print 'addAuthorsAndAffiliations: Adding PubName',PubName, Inst
                    else:
                        print 'addAuthorsAndAffiliation: length',len(splitline),'INVALID for line=',line
                        sys.exit('addAuthorsAndAffiliation: Invalid line')

                    if KeepGoing:
                        FamilyName = FamilyName.replace('_',' ') # handle multiple, unhyphenated family names
                        GivenName = GivenName.replace('_',' ')   # handle initials

                        IndexName = FamilyName + ' ' + GivenName
                        if self.debug>0: print 'addAuthorsAndAffiliations: Action',Action,'IndexName',IndexName
                            
                        if Action.upper()=='ADD':
                            # add author if necessary
                            if IndexName not in Authors:
                                if PubName is not None:
                                    Authors[IndexName] = [PubName, Inst, '', '']
                                else:
                                    Authors[IndexName] = [self.GetPubName(FamilyName, GivenName), Inst, '', '']
                                AuthorList.append(IndexName)
                            # add institution name if it is new
                            if Inst not in Authors[IndexName]:
                                Done = False
                                if '' in Authors[IndexName]:
                                    i = Authors[IndexName].index('')
                                    Authors[IndexName][i] = Inst
                                    Done = True
                                if not Done:
                                    words = 'addAuthorsAndAffiliations: ERROR could not add Institution ' + Inst \
                                            + ' for FamilyName ' + FamilyName + ' GivenName ' + GivenName \
                                            + ' because author already has three institutions ' + Authors[IndexName][1] \
                                            + ' ' + Authors[IndexName][2] + ' ' + Authors[IndexName][3]
                                    sys.exit(words)

                        elif Action.upper()=='REMOVE':
                            if IndexName in Authors:
                                if Inst in Authors[IndexName]:
                                    print 'addAuthorsAndAffiliations: Remove Inst',Inst,'from',IndexName
                                    i = Authors[IndexName].index(Inst)
                                    if i>=1:
                                        Authors[IndexName].pop(i)
                                        Authors[IndexName].append('')
                                    else:
                                        Authors[IndexName][i] = ''
                                else:
                                    print 'addAuthorsAndAffiliations: WARNING Inst',Inst,'cannot be removed from',IndexName
                                        
                        elif Action.upper()=='NOWAT':
                            if IndexName in Authors:
                                if '' in Authors[IndexName]:
                                    i = Authors[IndexName].index('')
                                    Authors[IndexName][i] = 'NOWAT_'+Inst
                                else:
                                    words = 'addAuthorsAndAffiliations: ERROR could not add NOW AT Institution ' + Inst \
                                      + ' FamilyName ' + FamilyName + ' GivenName ' + GivenName \
                                      + ' too many institutions ' + ' '.join('%' % x for x in Authors[IndexName][1:])
                                    sys.exit(words)
                            else:
                                words = 'addAuthorsAndAffiliation: ERROR cannot add NOW AT for FamilyName ' \
                                  + FamilyName + ' GivenName ' + GivenName + '. Name not in authorlist '
                                sys.exit(words)
                        elif Action.upper()=='SWAP':
                            #print 'addAuthorsAndAffilliation: ACTION',Action,'IndexName',IndexName,'Authors[IndexName]',Authors[IndexName]
                            pN,I1,I2,I3 = Authors[IndexName]
                            if I3=='':
                                Authors[IndexName] = pN,I2,I1,I3
                            else:
                                Authors[IndexName] = pN,I3,I1,I2
                            print 'addAuthorsAndAffilliation: ACTION',Action,'IndexName',IndexName,'original',pN,I1,I2,I3,'final',Authors[IndexName]
                                
                        else:
                            print 'addAuthorsAndAffiliations: Unknown Action',Action,'. No action taken for line',line[:-1]

            f.close()
        return

    def testAuthorList(self, names):
        '''
        test the generated authorlists.
        first make sure the necessary ancillary files for latex (*.sty, *.cls, *.rtx) are available,
        then run pdflatex 3 times to make sure all references get resolved
        20160311 add bibtex for Now at
        20161020 add option to skip test
        '''
        print '\n Press enter to run pdflatex to test generated authorlists. Enter `N` to skip pdflatex'
        reply = raw_input()
        if reply=='N': return
        

        if self.prefix!='':
            os.system('ln -s  ../*.sty .')
            os.system('ln -s  ../*.cls .')
            os.system('ln -s  ../*.rtx .')
            os.system('ln -s  ../*.bst .')
            os.system('ln -s  ../*.clo .')
        for name in names:
            cmd = 'pdflatex '+self.prefix+'test_'+name+'_authorlist.tex'
            bcmd= 'bibtex   '+'test_'+name+'_authorlist'  # .aux file is in current working dir
            print '\n\n ' + cmd + ' \n\n'
            os.system(cmd)
            if 'PhysRev' in name:
                print '\n\n ' + bcmd + ' \n\n'
                os.system(bcmd)
            print '\n\n ' + cmd + ' \n\n'
            os.system(cmd)
            print '\n\n ' + cmd + ' \n\n'
            os.system(cmd)
        return
    def getAddressForInst(self, Inst):
        '''
        return address for input institution
        20160617 matching of Inst with name in line was ambiguous. now fixed.
        '''
        f = open(self.AddressListFileName,'r')
        for line in f:
            if line[0]!='%' and Inst==line.split(']')[0].split('\\')[-1] :
                A = line.split('{')[1]
                Address = A.split('}')[0]
                return Address
        sys.exit('getAddressForInst: ERROR No address for Inst ' + Inst)
        return
    def writeCPCAddresses(self, filename, defList):
        '''
        write address for each institution to file name
        preface appropriately
        20160311 Add 'Now at' modifications, remove parentheses around each institution name (why were they there anyway?)
        '''
        filename.write( '\\maketitle %%%%%%%% NOTE THAT maketitle COMMAND APPEARS IN THE AUTHOR LIST %%%%%%%   \n' )
        filename.write( '\\address{\n' )
        filename.write( '\\vspace{0.3cm}\n' )
        filename.write( '{\\normalsize (Daya Bay Collaboration)} \\\\ \n' )
        filename.write( '\\vspace{0.3cm}\n' )
        ## preface complete
        eadd = open(self.AddressListFileName,'r')
        d = {}
        for line in eadd:
            if line[0]!='%':
                s = line.replace('\\address[','').split(']')[0].replace('\\','')  # Inst
                name = line.split('{')[1].split('}')[0]
#                newline = '$^{\\' + s + '}$(' + name + ') \\\\ \n'
                newline = '$^{\\' + s + '}$' + name + ' \\\\ \n'
                d[s] = newline
        eadd.close()
        #for s in d: print 'writeCPCAddresses:s,d=',s,d[s]

        for Inst in defList:
            if 'NOWAT_' not in Inst:
                if Inst!='DEAD':
                    address = d[Inst]
                    filename.write(address)
        # add suffix
        filename.write( '} \n')
        #print 'writeCPCAddresses: Done'
        return
    def writeElsevierAddresses(self, filename, defList,EJPC=False):
        '''
        Write the addresses associated with each institution to filename.
        The original addresslist comes from a file prepared by Bob Hackenburg
        for the muon system paper in spring 2014
        20170117 use this module to also write the addresses and labels for EJPC
        Note that the line taken from the file already has a carriage return at the end of each line
        '''
        eadd = open(self.AddressListFileName,'r')
        d = {}
        if EJPC: filename.write('\\institute{\n')
        for line in eadd:
            if line[0]!='%':
                s = line.replace('\\address[','').split(']')[0].replace('\\','')
                d[s]=line
                if EJPC: d[s] = line.replace('address','label').replace(']','}').replace('[\\','{')
                #print 's',s,'d[s]',d[s][:-1]
        for Inst in defList:
            if 'NOWAT_' not in Inst: # 'Now at' written as \fntext
                #print 'Inst',Inst
                if Inst!='DEAD':
                    address = d[Inst]
                    if EJPC and Inst!=defList[-1]: address += ' \\and '
                    filename.write(address)
        eadd.close()
        if EJPC: filename.write('}\n')
        return
    def writeJCAPAddresses(self, filename, defList):
        '''
        Write the addresses associated with each institution to filename.
        The original addresslist comes from a file prepared by Bob Hackenburg
        for the muon system paper in spring 2014
        '''
        eadd = open(self.AddressListFileName,'r')
        d = {}
        for line in eadd:
            if line[0]!='%':
                s = line.replace('\\address[','').split(']')[0].replace('\\','')
                d[s]=line.replace('\\address','\\affiliation')
                #print 's',s,'d[s]',d[s][:-1]
        for Inst in defList:
            if 'NOWAT_' not in Inst: # 'Now at' written as \fntext
                #print 'Inst',Inst
                if Inst!='DEAD':
                    address = d[Inst]
                    filename.write(address)
        eadd.close()
        return
    def acceptableDate(self, dateSafe, Irow, sheet):
        '''
        Determine if date and status credentials are satisfactory
        
        compare Days from Irow in sheet with tuple of dateSafe.
        if Days is later than dateSafe, then Days is NOT acceptable
        HOWEVER, check if the name for the input row is given elsewhere,
        if so, check that start date

        For all cases make sure duration on experiment is >1 year.

        20151130 Fix to use WorkBook.datemode that gives the correct starting date
        of 1900 to evaluate excel date.
        See http://www.lexicon.net/sjmachin/xlrd.html#xlrd.xldate%5Fas%5Ftuple-function
        '''

        Days = sheet.cell_value(Irow, self.DateStartCol)
        
        startTuple = xlrd.xldate_as_tuple(Days,self.WorkBook.datemode)

        EndDate = sheet.cell_value(Irow, self.DateEndCol)
        endTuple = None
        if EndDate!='0000-00-00':
            endTuple = xlrd.xldate_as_tuple(EndDate, 1)
            endm1 = (endTuple[0]-1, endTuple[1], endTuple[2], 0,0,0)
            if endm1<startTuple: return False # duration too short

        status = sheet.cell_value(Irow, self.StatusCol).lower()
        if self.debug>1: print 'start:',Days,startTuple,'safe:',dateSafe, 'end:',EndDate,endTuple,'status',status
        if status=='former':
            if startTuple<=dateSafe and endTuple is not None:
                if dateSafe<=endTuple : return True
        else:
            if xlrd.xldate_as_tuple(Days,self.WorkBook.datemode) < dateSafe : return True
        FamilyName =   sheet.cell_value(Irow, self.FamilyNameCol )
        GivenName =    sheet.cell_value(Irow, self.GivenNameCol  )
        
        for irow in range( 1,sheet.nrows ):
            if FamilyName==sheet.cell_value(irow, self.FamilyNameCol) and GivenName==sheet.cell_value(irow, self.GivenNameCol):
                Days = sheet.cell_value(irow, self.DateStartCol)
                EndDate = sheet.cell_value(irow, self.DateEndCol)
                status = sheet.cell_value(irow, self.StatusCol).lower()
                startTuple = xlrd.xldate_as_tuple(Days, self.WorkBook.datemode)
                endTuple = None
                if EndDate!='0000-00-00': endTuple = xlrd.xldate_as_tuple(EndDate, self.WorkBook.datemode)
                if status=='former':
                    if endTuple is not None:
                        if startTuple<=dateSafe and dateSafe<=endTuple: return True
                else:
                    if startTuple<=dateSafe : return True
                    
        return False
    def writeNewCommand(self, fp, defList):
        '''
        write \newcommand for each institution in authorlist based on list of institutions
        in defList and the address in self.AddressListFileName
        20160311 Add Now at support
        '''
        eadd = open(self.AddressListFileName,'r')
        for line in eadd:
            if self.debug>1: print line
            if line[0]!='%':
                Inst = line.split('[')[1].split(']')[0].replace('\\','')
                if Inst in defList:
                    newline = line.replace('}','}}').replace(']{','}{\\affiliation{').replace('\\address[','\\newcommand{')
                    fp.write(newline)
                elif 'NOWAT_'+Inst in defList:
                    newline = line.replace('}','}}').replace(']{','}{\\altaffiliation[Now at ]{').replace('\\address[','\\newcommand{')
                    newline += '\n'
                    fp.write(newline)
                    

        eadd.close()
        return

    def writeDefList(self, filename, defList,JCAP=False):
        '''
        for Elsevier or JCAP author list, write out list of institutions in order of citation
        20160311 Add 'Now at' processing.
        20161019 Add JCAP capability
        '''
        nNow = 0
        for i,Institution in enumerate(defList):
            Inst = Institution.replace('NOWAT_','')
            if 'NOWAT_' in Institution:
                Address = self.getAddressForInst(Inst)
                if JCAP:
                    nNow += 1
                    line = '\\def\\'+Inst+'{'+str(nNow)+'}\n'
                    line+= '\\def\\'+Inst+'note{\\note{Now at: '+Address+'}}\n'
                else:
                    line = '\\fntext['+Inst+']{Now at: '+Address+'}\n'
            else:
                j = i+1
                Sj = str(j)
                if JCAP: Sj = self.superAlpha[j]
                line = '\\def\\'+Inst+'{'+Sj+'}\n'
            filename.write(line)
        return True
    def writeCPCInstList(self, filename, defList):
        '''
        for CPC author list, write out list of institutions in order of citation with new command
        '''
        j = 0
        for i,Institution in enumerate(defList):
            Inst = Institution.replace('NOWAT_','')
            if 'NOWAT_' in Institution:
                Address = self.getAddressForInst(Inst)
                #line = '\\footnotetext['+Inst+']{Now at '+Address+'}\n'
                writeme = False
            else:
                j = j + 1
                line = '\\newcommand{\\' + Inst + '}{' + str(j) + '}\n'
                writeme = True
            if writeme: filename.write(line)
        return True
    def DuplicatePubName(self, iPubName):
        '''
        20150501 
        Return true if input PublicationName is already present in refSheet (spreadsheet with publications names).
        
        '''
        refSheet = self.PubNameSheet
        for irow in range(1, refSheet.nrows):
            if iPubName==refSheet.cell_value(irow, self.PublishNameCol_ref): return True
        return False
    def GetPubName(self, FamilyName, GivenName):
        '''
        From the input family name and given name, generate the "publication name"
        which is the name that will appear in the authorlist for the paper.
        The "publication names" are taken from a spreadsheet prepared by Bob Hackenburg. 
        '''
        debug = False
        refSheet = self.PubNameSheet
        matchingRows = []
        if (debug): print 'GetPubName: Inputs FamilyName',FamilyName,'GivenName',GivenName
        for irow in range(1, refSheet.nrows): 
            FName =  refSheet.cell_value(irow,self.FamilyNameCol_ref )
            GName =  refSheet.cell_value(irow,self.GivenNameCol_ref )
            if FName==FamilyName or GName==GivenName :
                words = 'GetPubName: partial match FamilyName "'+str(FamilyName)+'" FName "' +str(FName)+ '" GivenName "' + str(GivenName) + '" GName "' + str(GName) + '"'
                if (debug): print words
            if FName==FamilyName and GName==GivenName  :
                matchingRows.append( irow )

        if (debug): print 'GetPubName:',len(matchingRows),'PubName(s) that match input. Rows matching PubName are',matchingRows
        if len(matchingRows)==1 : # good. unique match
            irow = matchingRows[0]
            PubName = refSheet.cell_value(irow,self.PublishNameCol_ref)

        elif len(matchingRows)==0 : # no publication name
            words = 'REFERENCE CONTAINS NO PUBLICATION NAME FOR FamilyName '+FamilyName+' GivenName '+GivenName \
                    + ' You need to add a publication name to ' + self.PubNameFileName
            return None
            
        else: # multiple names??
            PubName = refSheet.cell_value(matchingRows[0], self.PublishNameCol_ref)
            for irow in matchingRows:
                irow = matchingRows[0]
                if PubName!=refSheet.cell_value(irow, self.PublishNameCol_ref):
                    words = 'REFERENCE CONTAINS MULTIPLE MATCHES FOR FamilyName '+FamilyName+' GivenName '+GivenName,\
                            ' WITH DIFFERENT PUBLICATION NAMES. You need to edit '+self.PubNameFileName \
                            +' to have a unique publication name ONLY FIRST TWO MATCHES WILL BE USED'
                    sys.exit(words)
        return PubName

        
if __name__ == '__main__':

    if len(sys.argv)<2 or sys.argv[1] in ["help","-help","--help","-u"]:
        print "Usage:  AuthGen.py <FileName> [ <StartDate> ] [ <debug level> ] [ AddChineseNames ]" 
#        print ""
        print "where:"
        print "  <FileName> is the name of the Excel file, including the .xls extension, containing the authors, etc. The Excel file is generated by giving a timestamp on Collaboration Database Administration page http://dayabay.ihep.ac.cn/admin/ "
#        print " " 
        print "  <StartDate> is a date which will cause any author with its 'StartDate' cell after <StartDate> to be excluded. The only format for <StartDate> is YYYYMMDD . If omitted, <StartDate> defaults to today "
        print " <debug level> = 0 by default, higher integers mean more debug output"
        print "  "
        print "RECOMMENDED WORKFLOW: "
        print "Starting in $SITEROOT/dybgaudi/Documentation/AuthorList : create a subdirectory with an evocative name such as ReactorFluxPaper"
        print " $ mkdir ReactorFluxPaper "
        print " $ mv <FileName> ReactorFluxPaper/."
        print " $ cd ReactorFluxPaper/"
        print " $ python ../AuthGen.py <FileName> <StartDate> [<debug level>] "
        print "Upon successful completion , two tex files are created:"
        print "  PhysRev.tex for Phys. Rev. journals"
        print "  Elsevier.tex for Elsevier journals."
        print "In addition, sample articles are generated to confirm that the two tex files are correct."
        print "UPON COMPLETION, YOUR SHOULD ADD AND COMMIT YOUR SUBDIRECTORY TO SVN"
        print "  "
        print " Ancillary files used by AuthGen.py: "
        print "  AuthorList/list_with_pubnames.xls is an Excel file that has the correspondance between the family and given names "
        print "                         and the author name in the publications "
        print "  AuthorList/addresslist_for_Elsevier.tex is an Excel file that provides the address for all institutions"
        print "  AuthorList/TestDir/extra_authors_and_affiliations.txt is an optional file that allows authors and/or affiliations"
        print "                         to be added or removed. You can copy this file from TestDir and modify it as required."
        
        print ""
        print "AuthGen.py with no arguments, or with 'help', '-help', or '--help', or '-u' produces this message."
        print ""
        print "AuthGen.py    version 25-Feb-2014      R. Hackenburg hack@bnl.gov"
        print "              heavily revised 20140528 djaffe@bnl.gov "
        print ""
        os._exit(0)

    FileName = sys.argv[1]
    DateString = datetime.date.today().strftime("%Y%m%d")
    debug = 0
    AddChineseNames = False
    if len(sys.argv)>2:
        DateString = sys.argv[2]
    if len(sys.argv)>3:
        debug = int(sys.argv[3])
    if len(sys.argv)>4:
        AddChineseNames = True

    Main(FileName,DateString,debug=debug,AddChineseNames=AddChineseNames)
    os._exit(0)
