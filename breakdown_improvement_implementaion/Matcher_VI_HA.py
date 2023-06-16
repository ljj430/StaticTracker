import XMLreader as xmlreader
import jpype
from Utils import Diff
import Utils as utils
import time
import pandas as pd
from io import StringIO
import git
import os
import numpy as np
from BugInstance import BugInstance
import sys
from munkres import Munkres, print_matrix
import MatchedPairsCollector

MATCHING_THRESHOLD = 20
DEBUG = False
TRACK = False
trackBuginstance = BugInstance()

def splitDollarMark(className):
    token = className.split("$")
    return token[0]


totoalViolationCount = 0
unchangedExactMatchCount = 0
changedExactMatchCount = 0
locationBasedCount = 0
snippetBasedCount = 0
hashBasedCount = 0
unmatchedCount = 0

unchangedExactMatchTotalTime = 0
changedExactMatchTotalTime = 0
locationBasedTotalTime = 0
snippetBasedTotalTime = 0
hashBasedTotalTime = 0
unmatchedTotalTime = 0



### only hungarian
def matchChildParent(repoPath, parentBuginstances, childBuginstances, parentCommit, childCommit):
    global trackBuginstance
    global totoalViolationCount
    global unchangedExactMatchCount
    global changedExactMatchCount
    global locationBasedCount
    global snippetBasedCount
    global hashBasedCount
    global unmatchedCount

    global unchangedExactMatchTotalTime
    global changedExactMatchTotalTime
    global locationBasedTotalTime
    global snippetBasedTotalTime
    global hashBasedTotalTime
    global unmatchedTotalTime
    utils.checkout(repoPath, childCommit)
    ###initial
    parentTracked = []
    parentTracked = set(parentTracked)
    childTracked = []
    childTracked = set(childTracked)
    unmatchedParent = set()
    matchedPairs = []
    trackingMap = {}
    ### Diff object
    diff = Diff(repoPath)
    ###parentChangedPaths is a list that contains the package path + class name of each parent changed file
    ### diffMap is a dic (a path -> a diff object)
    ###path: kafka.common.xxx.java/scala
    ####the diffMap's key is a path org.apache.kafka.clients.st.java. the value is a diff object
    ##### parentChangedPaths list is a list that saves diffMap's key
    parentChangedPaths, childChangedPaths, diffMap = \
        utils.transformFilesToPackagePaths(diff, parentCommit, childCommit, repoPath)
    diffPaths = []
    for path in parentChangedPaths:
        if diffMap[path].b_path is None:
            continue
        diffPaths.append(diffMap[path].b_path)
    sourceParentDic = utils.getAllSourceText(repoPath,diffPaths,parentCommit)

    diffPaths = []
    for path in childChangedPaths:
        if diffMap[path].a_path is None:
            continue
        diffPaths.append(diffMap[path].a_path)
    sourceChildDic = utils.getAllSourceText(repoPath,diffPaths,childCommit)

    # mapParentPath = utils.createMapPath(kafkaPath, parentCommit)
    # mapchildPath = utils.createMapPath(kafkaPath, childCommit)
    ###inline functions


    def recordSuccessMatch(pa, matchedBugInstances, mainClassName, matchedby):
        untrackedInstances = matchedBugInstances - childTracked
        if len(untrackedInstances) == 0:
            return False
        else:
            ####track childBuginstance
            ### check out whether it is already in tracked alarms.(if it is, exceptional case.)
            untrackedInstances = list(untrackedInstances)
            matchedChild = untrackedInstances[0]  # assuming there are one single match.
            parentTracked.add(pa)
            childTracked.add(matchedChild)
            trackingMap[pa] = matchedChild
            matchedPairs.append([pa, matchedChild])
            return True  ##matched

    def findExactMatching(pa, mainClassName):
        matchedChildAlarms = findExactMatchingAlarm(pa, childHash)
        if (len(matchedChildAlarms) == 0):  ###no matching
            return False
        else:
            return recordSuccessMatch(pa, matchedChildAlarms, mainClassName, matchedby="exact")

    ###end inline functions
    parentBuginstances = set(parentBuginstances)
    exactCandidates = []
    locationCandidates = []
    snippetCandidates = []
    childHash = {}
    for ch in childBuginstances:
        childHash[ch] = ch


    for pa in parentBuginstances:

        ###time evaluation
        startTime = time.time()
        ###
        ### 0.find out whether it is in changed set
        ###
        mainClassPath = pa.getSourcePath()
        mainClassPath = mainClassPath.replace("/", ".")
        isChanged = False
        for path in parentChangedPaths:
            if mainClassPath != "" and mainClassPath in path:
                isChanged = True

        #### take exact matching in unchagned files.
        if not isChanged:  ###if not in changed  ##mainClassPath is like kafka.common.xxx.java
            ###
            ### 1.Try to find matching bugInstance in child alarm set
            ### (only one method available since it is in the unchanged set).
            ### exact matching in non-changed set.
            ###
            # print("start to match changed file")

            successAny = findExactMatching(pa, mainClassPath)
            if successAny == True:
                unchangedExactMatchCount = unchangedExactMatchCount + 1
                endTime = time.time()
                unchangedExactMatchTotalTime = unchangedExactMatchTotalTime + endTime - startTime

    untrackedParent = parentBuginstances - parentTracked
    untrackedChild = childBuginstances - childTracked
    # print("After exact matching in unchanged file:")
    # print("the number of untrackedParent", len(untrackedParent))
    # print("the number of untrackedChild", len(untrackedChild))

    paCandidates, chCandidates, candidatesList = set(), set(), []
    count = 1
    for pa in untrackedParent:

        mainClassPath = pa.getSourcePath()
        mainClassPath = mainClassPath.replace("/", ".")  #####kafka.api.xxx
        isChanged = False
        for path in parentChangedPaths:
            if mainClassPath in path:
                isChanged = True
        if isChanged:
            ####
            #### 0.exact matching
            ####
            candidates = set()
            exactMatchingInstance = findExactMatchingAlarm(pa, childHash)
            if len(exactMatchingInstance) > 0:
                        for ch in exactMatchingInstance:
                            candidatesList.append([pa, ch,"exact"])
                            if ch not in chCandidates:
                                chCandidates.add(ch)
                        paCandidates.add(pa)
            d = diffMap[mainClassPath]

            edits = utils.getEditList(d)

            ###
            ### 1.Location-based  matching.
            ###
            if utils.getDiffType(d) == "A" or utils.getDiffType(d) == "D":
                pass
            else:
                locMatchingInstance = findLocBasedMatchingAlarms(pa, untrackedChild, edits)

                if len(locMatchingInstance) > 0:
                    for ch in locMatchingInstance:
                        candidatesList.append([pa, ch,"location"])
                        if ch not in chCandidates:
                            chCandidates.add(ch)
                    paCandidates.add(pa)

            ###2.snippet-based  matching.

            ###debug
            trackedPath = "com/google/common/collect/ImmutableSetTest.java"
            trackedLine = "269"
            trackedFlag = False
            if pa.getStartLine() == trackedLine and pa.getSourcePath() == trackedPath:
                trackedFlag = True

            candidates = set()
            snippetMatchingInstance = set()


        #if not is or len(snippetMatchingInstance) == 0:
            if utils.getDiffType(d) == "A" or utils.getDiffType(d) == "D":
                pass
            else:
                candidates = set()
                for ch in untrackedChild:
                    if utils.isSameButDiffLoc(pa, ch):
                        candidates.add(ch)
                parentSnippet = utils.getLineRange(sourceParentDic[d.b_path],
                                                    pa.getStartLine(), pa.getEndLine())
                parentSnippet = parentSnippet.replace(" ", "")

                for ch in candidates:
                    childSnippet = utils.getLineRange(sourceChildDic[d.a_path],
                                                        ch.getStartLine(), ch.getEndLine())
                    childSnippet = childSnippet.replace(" ", "")
                    if childSnippet == parentSnippet:
                        snippetMatchingInstance.add(ch)

            if len(snippetMatchingInstance) > 0:
                for ch in snippetMatchingInstance:
                    candidatesList.append([pa, ch,"snippet"])
                    if ch not in chCandidates:
                        chCandidates.add(ch)
                paCandidates.add(pa)
            # print(f"finish {count}/{len(untrackedParent)}")
            count += 1

    if len(paCandidates) > 0:
        paCandidates = list(paCandidates)
        chCandidates = list(chCandidates)

        matchedPaList, matchedChList,matchedPairs = hungarianAlgorithm(paCandidates, chCandidates, candidatesList,matchedPairs)
        untrackedParent = set(untrackedParent) - set(matchedPaList)
        untrackedChild = set(untrackedChild) - set(matchedChList)
    # print("After matching:")
    # print("the number of untrackedParent", len(untrackedParent))
    # print("the number of untrackedChild", len(untrackedChild))

    return untrackedChild, untrackedParent,matchedPairs

def hungarianAlgorithm(paCandidates, chCandidates,relations,matchedPairs): ###relations -> (parentInstance, childInstance, matchingtype)
    matrix = [[0 for j in range(len(chCandidates))] for i in range(len(paCandidates))]
    matchedPaList, matchedChList = [],[]

    for pair in relations:
        for i in range(len(paCandidates)):
            if paCandidates[i] == pair[0]:
                for j in range(len(chCandidates)):
                    if pair[1] == chCandidates[j]:
                        if pair[2] == 'exact':
                            matrix[i][j] +=1
                        elif pair[2] == "location":
                            matrix[i][j] += 1
                        elif pair[2] == "snippet":
                            matrix[i][j] += 2 
    costMatrix = []
    for row in matrix:
        cost_row = []
        for col in row:
            cost_row += [sys.maxsize - col]
        costMatrix += [cost_row]

    ###MUNKRES
    m = Munkres()
    indexes = m.compute(costMatrix)
    total = 0

    for row, column in indexes:
        value = matrix[row][column]
        total += value


        matched_flag = False
        for pair in relations:
            if paCandidates[row] == pair[0] and chCandidates[column] == pair[1]:
                matched_flag = True
                break
        if matched_flag:
            matchedPaList.append(paCandidates[row])
            matchedChList.append(chCandidates[column])
        matchedPairs.append([paCandidates[row],chCandidates[column]])
    # print(f'total cost:{total}')###changed813
    return matchedPaList,matchedChList,matchedPairs


def findExactMatchingAlarm(pa, childHash):
    output = []
    if pa in childHash:
        output.append(childHash[pa])
    output = set(output)
    return output





def lessThanMATCHING_THRESHOLD(x, matchingEdits, pa):
    childEdits = utils.getOverlappingEditsChild(x.getStartLine(), x.getEndLine(), matchingEdits)

    for i in childEdits:
        if abs(abs(int(pa.getStartLine()) - int(i.parentStart)) - abs(
                int(x.getStartLine()) - int(i.childStart))) <= MATCHING_THRESHOLD:
            return True
    return False



def findLocBasedMatchingAlarms(pa, childBuginstances, edits):
    candidate1 = []
    for ch in childBuginstances:
        if utils.isSameButDiffLoc(pa, ch):
            candidate1.append(ch)
    candidate1 = set(candidate1)
    matchingChild = set()
    ## TODO:if in edits 1.in:... 2. not in and find last edits 3. not in and cannot find last edits.
    if len(edits)>0:
        if utils.hasEditedParent(int(pa.getStartLine()), int(pa.getEndLine()), edits): ####pa is in diff
            matchingEdits = utils.getOverlappingEditsParent(pa.getStartLine(), pa.getEndLine(), edits)
            candidate2 = set(filter(lambda ch: utils.hasEditedChild(ch.getStartLine(), ch.getEndLine(), matchingEdits),
                                    candidate1))  ###changed813
            for ca in candidate2:
                if lessThanMATCHING_THRESHOLD(ca, matchingEdits, pa):
                    matchingChild.add(ca)
        else: ##pa is not in diff
            minimumEdit = utils.getMinimumEdit(edits)
            if int(pa.getStartLine()) < minimumEdit.parentStart and int(pa.getEndLine()) < minimumEdit.parentStart:### there is no diff before this pa.
                for ca in candidate1:
                    if abs(int(ca.getStartLine()) - int(pa.getStartLine())) <= MATCHING_THRESHOLD:
                        matchingChild.add(ca)
            else: ### there is a diff before this pa.
                adjacentEdit = utils.getAdjacentEdit(int(pa.getStartLine()),edits)
                for ca in candidate1:
                    if abs(abs(int(pa.getStartLine()) - adjacentEdit.parentEnd) - abs(int(ca.getStartLine()) - adjacentEdit.childEnd)):
                        matchingChild.add(ca)
    return matchingChild



if __name__ == "__main__":
    kafkaGithub = "https://github.com/apache/kafka"
    jcloudsGithub = "https://github.com/jclouds/jclouds"
    guavaGithub = "https://github.com/google/guava"
    springbootGithub = "https://github.com/spring-projects/spring-boot"

    reportsPath = r"D:\ThesisData\SampledReports\PMD\springboot"
    saveResultsPath = r"D:\ThesisData\tmp"
    repoPath = r"D:\ThesisProject\trackingProjects\spring-boot"
    githubPath = springbootGithub

    PMD = xmlreader.PMDReader
    Spotbugs = xmlreader.SpotbugsReader
    parentCommits = ["8b740c07e3e3ddcd7222521473c0e607ace9cd56"]
    childCommits = ["09b627d2326fc1e1aa17158d07732e7dd441751f"]


    # parentCommits = ["91b0b20cdff4d5cd8ff07befbf1fb3e6b27a7286", "9a2c0e531ee7202ec0aeae35b7e4bacf6b8dc88e","bd3633c4f98b8545c968356c73de18164abe07a2","d9113d51bf9f5537b4121807b2ed9862b80a6ad3"]
    # childCommits = ["cfe05dfda3ba79aa1bd3acce6b4e766eb7b9bc00", "ba2024d4e147cedc3fb442746872b46b11fef8a9","77a57f215fb6eb5a2c982ac1843299f21deb53d3","0a2258e6691a22aa7ff2604871b520d44bbac01f"]

    ##start JVM
    jarpath = os.path.join(os.path.abspath('.'),
                           r'D:\ThesisProject\findbugsanalysis\FixPatternMining\refactoringJava\out\production\refactoringJava')
    dependency = os.path.join(os.path.abspath('.'),
                              r'D:\ThesisProject\RefactoringMiner-2.0.2_libs\RefactoringMiner-2.0.2\lib')

    # jarpath = os.path.join(os.path.abspath('.'),
    #                        r'/Users/lijunjie/Desktop/Git/FixPatternMining/master/FixPatternMining/refactoringJava/out/production/refactoringJava')
    # dependency = os.path.join(os.path.abspath('.'),
    #                           r'/Users/lijunjie/Desktop/Master/AnalysisTools/RefactoringMiner/build/distributions/RefactoringMiner-2.0.2/lib')

    jvmPath = jpype.getDefaultJVMPath()
    if not jpype.isJVMStarted():
        jpype.startJVM(jvmPath, "-ea", "-Djava.class.path=%s" % jarpath, "-Djava.ext.dirs=%s" % dependency)

    jClass = jpype.JClass("edu.concordia.junjie.RefactoringInfo")
    # for i in range(len(parentCommits)):

    for i in range(len(parentCommits)):

        parentPMDFileName = os.path.join(reportsPath, parentCommits[i] + ".xml")
        childPMDFileName = os.path.join(reportsPath, childCommits[i] + ".xml")
        parentSpotbugsFileName = os.path.join(reportsPath, parentCommits[i] + ".xml")
        childSpotbugsFileName = os.path.join(reportsPath, childCommits[i] + ".xml")
        utils.checkout(repoPath, childCommits[i])

        ###Spotbugs
        startTime = time.time()
        parentBuginstances = PMD(parentSpotbugsFileName)
        childBuginstances = PMD(childSpotbugsFileName)


        endTime = time.time()
        readXMLTime = endTime - startTime

        matchingStartTime = time.time()
        unmatchedChild, unmatchedParent,matchedPairs = matchChildParent(repoPath, parentBuginstances, childBuginstances,
                                                           parentCommits[i], childCommits[i], githubPath, jClass)
        matchingEndTime = time.time()

        ##############################
        ### Debug
        ##############################
        print(f"commit:{childCommits[i]}")
        print("spot readXMLTime:", readXMLTime)
        totoalViolationCount = len(parentBuginstances)
        print("spot totoalViolationCount:", totoalViolationCount)
        print("spot totalMatchingTime: ", matchingEndTime - matchingStartTime)

        ################
        ### write to file
        ################
        utils.writeToGoneNew(unmatchedParent, unmatchedChild, parentCommits[i], childCommits[i], saveResultsPath,
                             saveResultsPath)
        matchedPairsSavePath = os.path.join(saveResultsPath, str(childCommits[i]) + '.xml')
        MatchedPairsCollector.wrtieToXML(matchedPairs, matchedPairsSavePath)

        #####PMD

        # startTime = time.time()
        # parentBuginstances = PMD(parentPMDFileName)
        # childBuginstances = PMD(childPMDFileName)
        #
        # # parentBuginstances = xmlreader.SpotbugsReader(parentFilename)
        # # childBuginstances = xmlreader.SpotbugsReader(childFilename)
        #
        # endTime = time.time()
        # readXMLTime = endTime - startTime
        #
        # matchingStartTime = time.time()
        # unmatchedChild, unmatchedParent,matchedPairs = matchChildParent(repoPath, parentBuginstances, childBuginstances,
        #                                                    parentCommits[i], childCommits[i], githubPath, jClass)
        # matchingEndTime = time.time()
        #
        # ##############################
        # ### Debug
        # ##############################
        # print(f"commit:{childCommits[i]}")
        # print("pmd readXMLTime:", readXMLTime)
        # totoalViolationCount = len(parentBuginstances)
        # print("pmd totoalViolationCount:", totoalViolationCount)
        # print("pmd totalMatchingTime: ", matchingEndTime - matchingStartTime)
        # print()
        #
        # ################
        # ### write to file
        # ################
        # utils.writeToGoneNew(unmatchedParent,unmatchedChild,parentCommits[i],childCommits[i],saveResultsPath,saveResultsPath)
        # row = [childCommits[i], matchingEndTime - matchingStartTime]
        #
        # utils.writeToTime(timeMeasurePath ,row)
    # shutdown JVM
    jpype.shutdownJVM() 