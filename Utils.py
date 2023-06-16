from git import Repo
from git.compat import defenc
import re
from BugInstance import BugInstance
import sys
import os
import XMLreader as xmlreader
import pandas as pd
import hashlib
import csv
HASH_SIZE = 100

def getAllSourceText(repoPath,filePathList, commit):

    sourceTextDic = {}
    checkout(repoPath, commit)
    repo = Repo(repoPath)
    hcommit = repo.head.commit
    for filePath in filePathList:
    # print("filePath:",filePath)###filePath: clients/src/test/java/org/apache/kafka/clients/consumer/KafkaConsumerTest.java
        sourceText = (hcommit.tree / filePath).data_stream.read().decode('UTF-8')
        sourceTextDic[filePath] = sourceText
    return sourceTextDic

def getSourceText(repoPath,filePath,commit):
    checkout(repoPath,commit)
    repo = Repo(repoPath)
    hcommit = repo.head.commit
    #print("filePath:",filePath)###filePath: clients/src/test/java/org/apache/kafka/clients/consumer/KafkaConsumerTest.java
    sourceText = (hcommit.tree / filePath).data_stream.read().decode('UTF-8')
    return sourceText

def getLineRange(cotents,start,end):
    counter=1
    output=""
    for line in cotents.splitlines():
        if counter >= int(start) and counter <= int(end):
            if output=="":
                output=line
            else:
                output+='\n'+line
        counter+=1
    return output

global checkoutCount
checkoutCount = 0
def checkout(repoPath,commit):
    # os.chdir(repoPath)
    # os.system('git checkout --f ' + commit)
    global checkoutCount
    repo = Repo(repoPath)

    #try:
    repo.git.checkout(commit, force=True)
    checkoutCount += 1
    #except:
     #   print(f"exception checkout count:{checkoutCount}")

def getChangedJavaFile(diffsList):#####find out the changed java or scala source file name from diffsList
    changedJavaFile = []
    for diff in diffsList:
        if diff is None:
            continue
        if diff.endswith(".java") or diff.endswith(".scala"):
            isSource = True
        else:
            isSource = False
        if isSource:
            changedJavaFile.append(diff)
    return changedJavaFile

def getPackagePath(sourceText):
    for line in sourceText.splitlines():
        line.strip()
        if line.startswith("package"):
            tokens = line.split(" ")
            token = tokens[-1]
            if line.endswith(";"):
                return token[:-1]
            else:
                return token
    return ""

def transformFilesToPackagePaths(diffs, parentCommit, childCommit, repoPath):
    diffOldPathList, diffNewPathList = diffs.getDiffPathList()
    changedJavaList = getChangedJavaFile(diffOldPathList)
    newChangedJavaList = getChangedJavaFile(diffNewPathList)
    # for i in newChangedJavaList:
    #     print(f"transform:{i}")

    oldPaths = []
    newPaths = []
    diffsMap = {}
    diff = diffs.getDiff()


    for d in diff:
        # print(f"a_path:{d.a_path}\tb_path{d.b_path}")
        if d.a_path in newChangedJavaList:
            if getDiffType(d) == "D": # IF the type is new file
                oldSource = ""

                newSource = getSourceText(repoPath, d.a_path, childCommit)
                newPackage = getPackagePath(newSource)
                tokens = d.a_path.split("/")
                newClass = tokens[-1]
                oldPackage = newPackage
                oldClass = newClass
                if oldPackage == "":
                    oldPackagePath = oldClass
                else:
                    oldPackagePath = oldPackage + "." + oldClass

                if newPackage == "":
                    newPackagePath = newClass
                else:
                    newPackagePath = newPackage + "." + newClass
                oldPaths.append(oldPackagePath)
                newPaths.append(newPackagePath)
                diffsMap[newPackagePath] = d

        if d.b_path in changedJavaList:
            oldSource = getSourceText(repoPath,d.b_path,parentCommit)
            oldPackage = getPackagePath(oldSource)
            tokens = d.b_path.split("/")
            oldClass = tokens[-1]

            # if d.new_file:
            #     print("deletedfile:", d.a_path, d.b_path)
            # elif d.deleted_file:
            #     print("newfile:", d.a_path, d.b_path)
            # elif d.renamed:
            #     print("renamed:", d.a_path, d.b_path)
            # else:
            #     print("else:", d.a_path, d.b_path)



            if getDiffType(d) == "A": #IF the type is deleted file
                #for l in changedJavaList:
                    #print("changed:", changedJavaList)
                #print("in new file:",d.a_path,d.b_path)
                #print("in deleted file:", d.a_path, d.b_path)
                newSource = ""
                oldSource = getSourceText(repoPath, d.b_path, parentCommit)
                oldPackage = getPackagePath(oldSource)
                tokens = d.b_path.split("/")
                oldClass = tokens[-1]
                newPackage = oldPackage
                newClass = oldClass
                if oldPackage == "":
                    oldPackagePath = oldClass
                else:
                    oldPackagePath = oldPackage + "." + oldClass

                if newPackage == "":
                    newPackagePath = newClass
                else:
                    newPackagePath = newPackage + "." + newClass
                oldPaths.append(oldPackagePath)
                newPaths.append(newPackagePath)

                diffsMap[oldPackagePath] = d

            else:

                newSource = getSourceText(repoPath, d.a_path, childCommit)
                newPackage = getPackagePath(newSource)
                tokens = d.b_path.split("/")
                newClass = tokens[-1]


                if oldPackage == "":
                    oldPackagePath = oldClass
                else:
                    oldPackagePath = oldPackage + "." + oldClass

                if newPackage == "":
                    newPackagePath = newClass
                else:
                    newPackagePath = newPackage + "." + newClass

                oldPaths.append(oldPackagePath)
                newPaths.append(newPackagePath)
                diffsMap[oldPackagePath] = d


                if d.a_path != d.b_path: ###rename class
                    diffsMap[newPackagePath] = d



    oldPaths = set(oldPaths)
    newPaths = set(newPaths)
    oldPaths = list(oldPaths)
    newPaths = list(newPaths)
    return oldPaths,newPaths,diffsMap

def getEditList(d):
    atPattern = re.compile(r'@@.*@@')
    msg = d.diff.decode(defenc)
    edits = []
    linesInfo = atPattern.findall(msg)
    numPattern = re.compile(r'\d+')
    for line in linesInfo :
        numList = numPattern.findall(line)
        childPatchStart = int(numList[0])
        childPatchEnd = childPatchStart + int(numList[1])
        parentPatchStart = int(numList[2])
        parentPatchEnd = parentPatchStart + int(numList[3])
        edit = Edit(d.b_path, parentPatchStart,parentPatchEnd,childPatchStart,childPatchEnd)
        edits.append(edit)
    return edits

def getMinimumEdit(Edits):
    minimumPa = sys.maxsize
    minimumCh = sys.maxsize
    minimumEdit = Edits[0]
    for edit in Edits:
        if edit.parentEnd<minimumPa  and edit.childEnd<minimumCh:
            minimumPa = edit.parentEnd
            minimumCh = edit.childEnd
            minimumEdit = edit
    return minimumEdit

def getAdjacentEdit(parentStart,Edits):
    ajacentEdit = getMinimumEdit(Edits)
    for edit in Edits:
        if edit.parentEnd < parentStart and edit.parentEnd > ajacentEdit.parentEnd:
            ajacentEdit = edit
    return ajacentEdit

def splitDollarMark(methodORvariable):
    token=methodORvariable.split("$")
    return token[0]

def isSameAlarm(p,c):
    #print("parent\n")
    #print(p)
    #print("child\n")
    #print(c)
    childMethod = splitDollarMark(c.getMethod())
    parentMethod = splitDollarMark(p.getMethod())
    childField = splitDollarMark(c.getField())
    parentField = splitDollarMark(p.getField())
    if c.getSourcePath() == p.getSourcePath()  and childMethod == parentMethod and childField == parentField and c.getBugAbbv() == p.getBugAbbv() and c.getStartLine() == p.getStartLine() and c.getEndLine() == p.getEndLine() :
        return True
    else:
        return False

def isSameButDiffLoc(p,c):
    childMethod = splitDollarMark(c.getMethod())
    parentMethod = splitDollarMark(p.getMethod())
    childField = splitDollarMark(c.getField())
    parentField = splitDollarMark(p.getField())
    if c.getSourcePath() == p.getSourcePath() and childMethod == parentMethod and childField == parentField  and c.getBugAbbv() == p.getBugAbbv() :
        return True
    else:
        return False

def isSameTypeAlarm(p,c):
    if c.getBugAbbv() == p.getBugAbbv():
        return True
    else:
        return False

def getOverlappingEditsParent(startLine,endLine, edits):
    return list(filter(lambda x: isOverlappedParent(startLine,endLine, x),edits))

def isOverlappedParent(statLine,endLine,e):
    up = e.parentStart
    bottom = e.parentEnd
    return isOverlapped(statLine, endLine, up , bottom)

def getOverlappingEditsChild(startLine,endLine, edits):
    return list(filter(lambda x: isOverlappedChild(startLine,endLine, x),edits))

def isOverlappedChild(statLine,endLine,e):
    up = e.childStart
    bottom = e.childEnd
    return isOverlapped(statLine, endLine, up , bottom)

def isOverlapped(startLine, endLine, up , bottom):
    if int(startLine) > up and int(startLine) > bottom:####change 'and' to 'or'
        # 1. edit is before violation?
        return False
    elif int(endLine) < up and int(endLine) < bottom:
        # 2. edit is after violation?
        return False
    else:
        return True

def hasEditedParent(startLine, endLine, edits):
    flag = False
    for edit in edits:
        if isOverlappedParent(startLine,endLine , edit):
            flag = True
            return flag
    return flag

def hasEditedChild(startLine, endLine, edits):
    flag = False
    for edit in edits:
        if isOverlappedChild(startLine,endLine , edit):
            flag = True
            return flag
    return flag
def hashToken(s):
    sha = hashlib.sha1(s.encode("utf8"))
    encrypts = sha.hexdigest()
    return str(encrypts)

def getFirstTokens(n , tokens):
    tokens = tokens[0:n]
    return "".join(str(token) + ' ' for token in tokens)[:-1]

def getLastTokens(n , tokens):
    tokens = tokens[len(tokens)-n:len(tokens)]
    return "".join(str(token) + ' ' for token in tokens)[:-1]

def hashFirstTokens(n , tokens): #return a string
    head = getFirstTokens(n,tokens)
    return hashToken(head)

def hashLastTokens(n , tokens): #return a string
    tail = getLastTokens(n,tokens)
    return hashToken(tail)

class Edit:
    def __init__(self,className,parentStart,parentEnd,childStart,childEnd):
        self.className=className
        self.parentStart=parentStart
        self.parentEnd=parentEnd
        self.childStart=childStart
        self.childEnd=childEnd
    def setClassName(self,className):
        self.className=className
    def setParentStart(self,start):
        self.parentStart = start
    def setParentEnd(self,end):
        self.parentEnd = end
    def setChildStart(self,start):
        self.childStart = start
    def setChildEnd(self,end):
        self.childEnd = end

class Diff:
    def __init__(self,repoPath):
        self.repoPath=repoPath
        self.repo = Repo(self.repoPath)


    def getDiffPathList(self):
        hcommit = self.repo.head.commit
        diffs = hcommit.diff('HEAD~1' , create_patch=True)
        diffOldPath = []
        diffNewPath = []
        for diff in diffs:
            diffOldPath.append(diff.b_path)
            diffNewPath.append(diff.a_path)
        return diffOldPath,diffNewPath

    def getDiff(self):
        hcommit = self.repo.head.commit
        diffs = hcommit.diff('HEAD~1',create_patch=True)
        return diffs

def getDiffType(d):
    if d.new_file:
        return 'A'   ###new file
    if d.deleted_file:
        return 'D'   ###deleted file
    if d.renamed:
        return 'R'
    else :
        return 'M'

def getAllPathList(repoPath,commit):
    allPathList=[]
    checkout(repoPath,commit)
    repo = Repo(repoPath)
    hcommit = repo.head.commit
    for entry in hcommit.tree.traverse():
        if entry.path.endswith(".scala") or entry.path.endswith(".java"):
            allPathList.append(entry.path)
    return allPathList



    ###test diffrangeList

    #print(parentChangedPaths)

###xxx/java/xxx/xxx -> java/xxx/xxx
def getClassPath(path):
    tmpPath = path.split('/')
    sourcePath = ''
    for each in tmpPath[::-1]:
        if 'java' == each:
            break
        elif '.java' in each:
            sourcePath = each
        elif 'com' == each:
            sourcePath = each + '/' + sourcePath
            break
        elif 'org' == each:
            sourcePath = each + '/' + sourcePath
            break
        elif 'scala' == each:
            sourcePath =  sourcePath
            break
        else:
            sourcePath = each + '/' + sourcePath
    return sourcePath


def getMethodName(method):
    tmpMethod = method.replace("public ", "")
    tmpMethod = tmpMethod.replace("private ", "")
    tmpMethod = tmpMethod.replace("protected ", "")


    tmpMethod = tmpMethod.split("\\(")
    tmpMethod = tmpMethod[0]
    return tmpMethod

def getFieldName(field):
    tmp = field.replace("public ","")
    tmp = tmp.replace("private ", "")
    tmp = tmp.replace("protected ", "")

    tmp = tmp.split(":")
    tmp = tmp[0]
    tmp = tmp.replace(' ','')
    return tmp

def createACopy(pa):
    copy = BugInstance()
    copy.setSourcePath(pa.getSourcePath())
    copy.setField(pa.getField())
    copy.setMethod(pa.getMethod())
    copy.setClass(pa.getClass())
    copy.setStartLine(pa.getStartLine())
    copy.setEndLine(pa.getEndLine())
    copy.setBugAbbv(pa.getBugAbbv())
    copy.setCategoryAbbrev(pa.getCategoryAbbrev())
    copy.setPriority(pa.getPriority())
    return copy

def createARomovedDollarCopy(pa):
    copy = BugInstance()
    copy.setSourcePath(pa.getSourcePath())

    if "$" in pa.getField():
        tokens = pa.getField().split("$")
        if tokens[0] == "":
            copy.setField(tokens[1])
        elif tokens[0]!="":
            copy.setField(tokens[0])
    else:
        copy.setField(pa.getField())

    if "$" in pa.getMethod():
        tokens = pa.getMethod().split("$")
        if tokens[0] == "":
            copy.setMethod(tokens[1])
        elif tokens[0] != "":
            copy.setMethod(tokens[0])
    else:
        copy.setMethod(pa.getMethod())

    copy.setClass(pa.getClass())
    copy.setStartLine(pa.getStartLine())
    copy.setEndLine(pa.getEndLine())
    copy.setBugAbbv(pa.getBugAbbv())
    copy.setCategoryAbbrev(pa.getCategoryAbbrev())
    copy.setPriority(pa.getPriority())
    return copy

def classRefactoringDetector(paRefactoring,eachRefactoring,isRefactoring):
    sourceCodePath = ""
    refactoringType = ""

    ###debug
    trackedPath = r"com/google/common/collect/MapMakerInternalMapTest.java"
    trackedMethod = r"testExpand_cleanup"
    trackedFlag = False
    if paRefactoring.getSourcePath() == trackedPath and paRefactoring.getMethod() == trackedMethod and paRefactoring.getStartLine() == "666":
        trackedFlag = True
        print(f"paRefactoring in class refactoring:\n{paRefactoring}\n")

    if paRefactoring.getSourcePath() == getClassPath(
            eachRefactoring.getRefactoringLeft().get(0).getFilePath() )and int(paRefactoring.getStartLine()) >= eachRefactoring.getRefactoringLeft().get(0).getStartLine() and (int(paRefactoring.getEndLine()) <= eachRefactoring.getRefactoringLeft().get(0).getEndLine() or eachRefactoring.getRefactoringLeft().get(0).getEndLine() < 0):
        ###debug
        if trackedFlag:
            print("this pa refactoring is class Refactoring")

        paRefactoring.setSourcePath(str(getClassPath(
            eachRefactoring.getRefactoringRight().get(0).getFilePath())))

        paNewStart = int(paRefactoring.getStartLine()) - int(eachRefactoring.getRefactoringLeft().get(0).getStartLine()) + int(eachRefactoring.getRefactoringRight().get(0).getStartLine())
        paNewEnd = int(paRefactoring.getEndLine()) - int(eachRefactoring.getRefactoringLeft().get(0).getStartLine()) + int(eachRefactoring.getRefactoringRight().get(0).getStartLine())
        paRefactoring.setStartLine(str(paNewStart))
        paRefactoring.setEndLine(str(paNewEnd))
        isRefactoring = True
        sourceCodePath = eachRefactoring.getRefactoringRight().get(0).getFilePath()
        refactoringType = eachRefactoring.getRefactoringType().toString()
    return paRefactoring,isRefactoring,sourceCodePath,refactoringType


def methodRefactoringDetector(paRefactoring,eachRefactoring,isRefactoring):
    ###debug
    trackedPath = r"com/google/common/collect/MapMakerInternalMapTest.java"
    trackedMethod = r"testExpand_cleanup"
    trackedFlag = False
    if paRefactoring.getSourcePath() == trackedPath and paRefactoring.getMethod() == trackedMethod and paRefactoring.getStartLine() == "666":
        trackedFlag = True
        print(f"paRefactoring in method refactoring:\n{paRefactoring}\n")

    sourceCodePath = ""
    refactoringType = ""
    if paRefactoring.getMethod() == getMethodName(eachRefactoring.getRefactoringLeft().get(0).getCodeElement()) and paRefactoring.getSourcePath() == getClassPath(eachRefactoring.getRefactoringLeft().get(0).getFilePath()) and int(paRefactoring.getStartLine()) >= eachRefactoring.getRefactoringLeft().get(0).getStartLine() and (int(paRefactoring.getEndLine()) <= eachRefactoring.getRefactoringLeft().get(0).getEndLine() or eachRefactoring.getRefactoringLeft().get(0).getEndLine() < 0):

        ###debug
        if trackedFlag:
            print("this pa refactoring is method Refactoring")

        paRefactoring.setMethod(getMethodName(str(eachRefactoring.getRefactoringRight().get(0).getCodeElement())))
        paRefactoring.setSourcePath(str(getClassPath(eachRefactoring.getRefactoringRight().get(0).getFilePath())))

        isRefactoring = True

        paNewStart = int(paRefactoring.getStartLine()) - int(eachRefactoring.getRefactoringLeft().get(0).getStartLine()) + int(eachRefactoring.getRefactoringRight().get(0).getStartLine())
        paNewEnd = int(paRefactoring.getEndLine()) - int(eachRefactoring.getRefactoringLeft().get(0).getStartLine()) + int(eachRefactoring.getRefactoringRight().get(0).getStartLine())
        paRefactoring.setStartLine(str(paNewStart))
        paRefactoring.setEndLine(str(paNewEnd))

        sourceCodePath = eachRefactoring.getRefactoringRight().get(0).getFilePath()
        refactoringType = eachRefactoring.getRefactoringType().toString()


    return paRefactoring, isRefactoring, sourceCodePath, refactoringType


def fieldRefactoringDetector(paRefactoring,eachRefactoring,isRefactoring):
    ###debug
    trackedPath = r"com/google/common/collect/MapMakerInternalMapTest.java"
    trackedMethod = r"testExpand_cleanup"
    trackedFlag = False
    if paRefactoring.getSourcePath() == trackedPath and paRefactoring.getMethod() == trackedMethod and paRefactoring.getStartLine() == "666":
        trackedFlag = True
        print(f"paRefactoring in field refactoring:\n{paRefactoring}\n")

    sourceCodePath = ""
    refactoringType = ""
    ### pa is a field refactoring
    if paRefactoring.getField() == getFieldName(
            eachRefactoring.getRefactoringLeft().get(0).getCodeElement()) and paRefactoring.getSourcePath() == getClassPath(eachRefactoring.getRefactoringLeft().get(0).getFilePath()):

        ###debug
        if trackedFlag:
            print("this pa refactoring is field Refactoring")



        paRefactoring.setField(
            getFieldName(str(eachRefactoring.getRefactoringRight().get(0).getCodeElement())))
        paRefactoring.setSourcePath(str(getClassPath(
            eachRefactoring.getRefactoringRight().get(0).getFilePath())))

        paNewStart = int(paRefactoring.getStartLine()) - int(eachRefactoring.getRefactoringLeft().get(0).getStartLine()) + int(eachRefactoring.getRefactoringRight().get(0).getStartLine())
        paNewEnd = int(paRefactoring.getEndLine()) - int(eachRefactoring.getRefactoringLeft().get(0).getStartLine()) + int(eachRefactoring.getRefactoringRight().get(0).getStartLine())
        paRefactoring.setStartLine(str(paNewStart))
        paRefactoring.setEndLine(str(paNewEnd))


        isRefactoring = True
        sourceCodePath = eachRefactoring.getRefactoringRight().get(0).getFilePath()
        refactoringType = eachRefactoring.getRefactoringType().toString()

    return paRefactoring, isRefactoring, sourceCodePath, refactoringType


def getPaRefactoring(paRefactoring,refactoringInfo):
    sourceCodePath = ""
    refactoringType = ""
    classRefactoringList = ["MOVE_CLASS","RENAME_CLASS","MOVE_RENAME_CLASS","EXTRACT_SUPERCLASS","EXTRACT_CLASS","EXTRACT_SUBCLASS"]
    methodRefactoringList = ["EXTRACT_OPERATION", "RENAME_METHOD","MOVE_OPERATION","PULL_UP_OPERATION","PUSH_DOWN_OPERATION",
                             "MOVE_AND_INLINE_OPERATION","EXTRACT_AND_MOVE_OPERATION","MOVE_AND_RENAME_OPERATION"]
    fieldRefactoringList = ["RENAME_ATTRIBUTE","RENAME_VARIABLE","RENAME_PARAMETER","MOVE_ATTRIBUTE","REPLACE_VARIABLE_WITH_ATTRIBUTE",
                            "MOVE_RENAME_ATTRIBUTE","PULL_UP_ATTRIBUTE","PUSH_DOWN_ATTRIBUTE"]

    isRefactoring = False
    for eachRefactoring in refactoringInfo:
        if eachRefactoring.getRefactoringType().toString() in fieldRefactoringList:
            ### pa is a field refactoring
            paRefactoring, isRefactoring, sourceCodePath, refactoringType = fieldRefactoringDetector(
                paRefactoring,
                eachRefactoring,isRefactoring)

        elif eachRefactoring.getRefactoringType().toString() in methodRefactoringList:
            ### pa is a method refactoring
            paRefactoring, isRefactoring, sourceCodePath, refactoringType = methodRefactoringDetector(paRefactoring,
                                                                                                          eachRefactoring,isRefactoring)

        elif eachRefactoring.getRefactoringType().toString() in classRefactoringList:
            ### pa is class refactoring
            paRefactoring, isRefactoring, sourceCodePath, refactoringType = classRefactoringDetector(paRefactoring,
                                                                                                          eachRefactoring,isRefactoring)

        if isRefactoring and refactoringType != "":
            break

    return paRefactoring,isRefactoring,sourceCodePath,refactoringType



def getPaRefactoringWihoutOthers(paRefactoring,refactoringInfo):
    sourceCodePath = ""
    refactoringType = ""
    classRefactoringList = ["MOVE_CLASS","RENAME_CLASS","MOVE_RENAME_CLASS"]
    methodRefactoringList = ["EXTRACT_OPERATION", "RENAME_METHOD"]
    fieldRefactoringList = ["RENAME_ATTRIBUTE","RENAME_VARIABLE","RENAME_PARAMETER"]
    for eachRefactoring in refactoringInfo:
        ###identify whether pa in refactoring List


        if eachRefactoring.getRefactoringType().toString() in classRefactoringList:
            ### pa is class refactoring
            paRefactoring, isRefactoring, sourceCodePath, refactoringType = classRefactoringDetector(paRefactoring, eachRefactoring)
            if refactoringType != "":
                # print("there is a class refactoring matched pairs!")
                classLeft = getClassPath(eachRefactoring.getRefactoringLeft().get(0).getFilePath())
                classRight = getClassPath(eachRefactoring.getRefactoringRight().get(0).getFilePath())
                # print(
                #     f"refactoringType:{refactoringType}\nclassLeft:{classLeft}\tclassRight:{classRight}\npaRefactoring:\n{paRefactoring}")
                # print()
            break

        elif eachRefactoring.getRefactoringType().toString() in methodRefactoringList:
            ### pa is a method refactoring
            paRefactoring, isRefactoring, sourceCodePath, refactoringType = methodRefactoringDetector(paRefactoring,eachRefactoring)
            if refactoringType != "":
                # print("there is a method refactoring matched pairs!")
                classLeft = getClassPath(eachRefactoring.getRefactoringLeft().get(0).getFilePath())
                classRight = getClassPath(eachRefactoring.getRefactoringRight().get(0).getFilePath())
                methodLeft = getMethodName(getMethodName(eachRefactoring.getRefactoringLeft().get(0).getCodeElement()))
                methodRight = getMethodName(getMethodName(eachRefactoring.getRefactoringRight().get(0).getCodeElement()))
                # print(f"refactoringType:{refactoringType}\nclassLeft:{classLeft}\tclassRight:{classRight}\nmethodLeft:{methodLeft}\tmethodRight:{methodRight}\npaRefactoring:\n{paRefactoring}")
                # print()
            break


        elif eachRefactoring.getRefactoringType().toString() in fieldRefactoringList:
            ### pa is a field refactoring
            paRefactoring, isRefactoring, sourceCodePath, refactoringType = fieldRefactoringDetector(paRefactoring,eachRefactoring)
            if refactoringType != "":
                # print("there is a field refactoring matched pairs!")
                classLeft = getClassPath(eachRefactoring.getRefactoringLeft().get(0).getFilePath())
                classRight = getClassPath(eachRefactoring.getRefactoringRight().get(0).getFilePath())
                fieldLeft = getFieldName(eachRefactoring.getRefactoringLeft().get(0).getCodeElement())
                fieldRight = getFieldName(eachRefactoring.getRefactoringRight().get(0).getCodeElement())
                # print(
                #     f"refactoringType:{refactoringType}\nclassLeft:{classLeft}\tclassRight:{classRight}\nfieldLeft:{fieldLeft}\tfieldRight:{fieldRight}\npaRefactoring:\n{paRefactoring}")
                # print()
            break
    return paRefactoring,isRefactoring,sourceCodePath,refactoringType



####write to
def writeToGoneNew(unmatchedParent,unmatchedChild,parentCommit,childCommit,gonePath,newPath):
    bugAbbvSetParent = []
    categorySetParent = []
    classSetParent = []
    methodSetParent = []
    fieldSetParent = []
    sourcePathSetParent = []
    startSetParent = []
    endSetParent = []
    for eachUnmatched in unmatchedParent:
        bugAbbvSetParent.append(eachUnmatched.getBugAbbv())
        categorySetParent.append(eachUnmatched.getCategoryAbbrev())
        classSetParent.append(eachUnmatched.getClass())
        methodSetParent.append(eachUnmatched.getMethod())
        fieldSetParent.append(eachUnmatched.getField())
        sourcePathSetParent.append(eachUnmatched.getSourcePath())
        startSetParent.append(eachUnmatched.getStartLine())
        endSetParent.append(eachUnmatched.getEndLine())

    dataframe = pd.DataFrame(
        {'Bug': bugAbbvSetParent, 'category': categorySetParent, "class name": classSetParent,
         "method name": methodSetParent, "field name": fieldSetParent, "source path": sourcePathSetParent,
         "start": startSetParent, "end": endSetParent})
    goneFile = os.path.join(gonePath, parentCommit[0:7] + "_" + childCommit[0:7] + "_gone_warnings.csv")
    dataframe.to_csv(goneFile, index=False,
                     sep=',')

    bugAbbvSetChild = []
    categorySetChild = []
    classSetChild = []
    methodSetChild = []
    fieldSetChild = []
    sourcePathSetChild = []
    startSetChild = []
    endSetChild = []
    for eachUnmatched in unmatchedChild:
        bugAbbvSetChild.append(eachUnmatched.getBugAbbv())
        categorySetChild.append(eachUnmatched.getCategoryAbbrev())
        classSetChild.append(eachUnmatched.getClass())
        methodSetChild.append(eachUnmatched.getMethod())
        fieldSetChild.append(eachUnmatched.getField())
        sourcePathSetChild.append(eachUnmatched.getSourcePath())
        startSetChild.append(eachUnmatched.getStartLine())
        endSetChild.append(eachUnmatched.getEndLine())

    dataframe = pd.DataFrame(
        {'Bug': bugAbbvSetChild, 'category': categorySetChild, "class name": classSetChild, \
         "method name": methodSetChild, "field name": fieldSetChild, "source path": sourcePathSetChild, \
         "start": startSetChild, "end": endSetChild})
    newFile = os.path.join(newPath, parentCommit[0:7] + "_" + childCommit[0:7] + "_new_warnings.csv")
    dataframe.to_csv(newFile, index=False,
                     sep=',')

def writeCSV(unmatchedParent,gonePath):
    bugAbbvSetParent = []
    categorySetParent = []
    classSetParent = []
    methodSetParent = []
    fieldSetParent = []
    sourcePathSetParent = []
    startSetParent = []
    endSetParent = []
    for eachUnmatched in unmatchedParent:
        bugAbbvSetParent.append(eachUnmatched.getBugAbbv())
        categorySetParent.append(eachUnmatched.getCategoryAbbrev())
        classSetParent.append(eachUnmatched.getClass())
        methodSetParent.append(eachUnmatched.getMethod())
        fieldSetParent.append(eachUnmatched.getField())
        sourcePathSetParent.append(eachUnmatched.getSourcePath())
        startSetParent.append(eachUnmatched.getStartLine())
        endSetParent.append(eachUnmatched.getEndLine())

    dataframe = pd.DataFrame(
        {'Bug': bugAbbvSetParent, 'category': categorySetParent, "class name": classSetParent,
         "method name": methodSetParent, "field name": fieldSetParent, "source path": sourcePathSetParent,
         "start": startSetParent, "end": endSetParent})
    goneFile = os.path.join(gonePath, "list_warnings.csv")
    dataframe.to_csv(goneFile, index=False,
                     sep=',')
def writeToTime(savePath, row): ###row (commit -> time)
    if not os.path.exists(savePath):
        with open(savePath, "w") as csvfile:
            fieldnames = ['Commit', 'Time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    with open(savePath, 'a', newline='') as f:
        fieldnames = ['Commit', 'Time']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow({'Commit': row[0], 'Time': row[1]})
if __name__ == "__main__":
    v = getFieldName("herder : Herder")
    print(v)







    ####test type
    '''for pa in parentBugInstances:
        mainClassPath = pa.getSourcePath()
        #mainClassPath = "kafka/api/ApiVersion.scala"
        mainClassPath = mainClassPath.replace("/",".")
        #####kafka.api.xxx

        if mainClassPath in parentChangedPaths:

            d = diffMap[mainClassPath]
            #print("d:",d)
            print("a_path:",d.a_path)
            print("change type:", d.change_type)
            #edits = getEditList(d)'''









    ###parentChangedPaths is a list that contains the package path + class name of each parent changed file
    ### diffMap is a dic (a path -> a diff object)

    #for path in parentChangedPaths:
        #print(path)



    ####find out the source text
    # repo=Repo(kafkaPath)
    # revlist=(
    #     (commit,  (commit.tree/path).data_stream.read())
    #     for commit in repo.iter_commits(paths=path)
    # )
    #
    # diff=Diff(kafkaPath)
    # print(diff.getDiffPathList())




