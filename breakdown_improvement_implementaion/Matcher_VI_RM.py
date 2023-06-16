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
# from munkres import Munkres, print_matrix
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

unchangedExactMatchTotalTime = 0
changedExactMatchTotalTime = 0
locationBasedTotalTime = 0
snippetBasedTotalTime = 0
hashBasedTotalTime = 0
unmatchedTotalTime = 0
unmatched_exact =0
changed_exact_match_list=[]

### This is the implementation that only consider refactoring
def matchChildParent(repoPath, parentBuginstances, childBuginstances, parentCommit, childCommit, githubUrl, jClass):
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
    global changed_exact_match_list
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
        #print(diffMap[path].b_path)
        #print(diffMap)
        if diffMap[path].b_path is None:
            continue
        diffPaths.append(diffMap[path].b_path)
    sourceParentDic = utils.getAllSourceText(repoPath,diffPaths,parentCommit)

    diffPaths = []
    for path in childChangedPaths:
        #print(diffMap[path].a_path)
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
            matchedChild = list(untrackedInstances)[0]  # assuming there are one single match.
            parentTracked.add(pa)
            childTracked.add(matchedChild)
            matchedPairs.append([pa,matchedChild])
            trackingMap[pa] = matchedChild
            return True ##matched

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


    githubPath = githubUrl
    instance = jClass()
    refactoringInfo = instance.getRefactoringInfo(repoPath, githubPath, childCommit)
    count = 1
    unmatched_count = 0

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
        else:
            ###
            ### 2.Try to find exact matching buginstance in changed files.
            ###
            exactMatches = findExactMatchingAlarm(pa, childHash)
            if len(exactMatches) > 0:
                successExact = recordSuccessMatch(pa,exactMatches,mainClassPath,matchedby = "exact")
                if successExact == True:
                    changedExactMatchCount = changedExactMatchCount + 1
                    endTime = time.time()
                    changedExactMatchTotalTime = changedExactMatchTotalTime + endTime - startTime
                    changed_exact_match_list.append(pa)
            else:
                successExact = False
    untrackedParent = parentBuginstances - parentTracked
    untrackedChild = childBuginstances - childTracked


    for pa in untrackedParent:
        mainClassPath = pa.getSourcePath()
        mainClassPath = mainClassPath.replace("/", ".")  #####kafka.api.xxx
        isChanged = False
        for path in parentChangedPaths:
            if mainClassPath in path:
                isChanged = True
        if isChanged:
        

      
            ###
            ### 1.Location-based refactoring matching.
            ###

            d = diffMap[mainClassPath]
            
            paRefactoring = utils.createACopy(pa)

            paRefactoring, isRefactoring, sourceCodePath, refactoringType = utils.getPaRefactoring(
                paRefactoring,
                refactoringInfo)

            edits = utils.getEditList(d)
            successLoc = False
            untrackedChild = childBuginstances - childTracked
            if isRefactoring:
                #added 11
                
                locMatchingInstance = findLocBasedRefactoringMatchingAlarms(paRefactoring, untrackedChild)
                if len(locMatchingInstance) > 0:
                    successLoc = recordSuccessMatch(pa, locMatchingInstance, mainClassPath, matchedby="location")
                    if successLoc == True:
                        locationBasedCount = locationBasedCount + 1
                        endTime = time.time()
                        locationBasedTotalTime = locationBasedTotalTime + endTime - startTime
                else:
                    if utils.getDiffType(d) == "A" or utils.getDiffType(d) == "D":
                        pass
                    else:
                        locMatchingInstance = findLocBasedMatchingAlarms(pa, untrackedChild, edits)

                        if len(locMatchingInstance) > 0:
                            successLoc = recordSuccessMatch(pa, locMatchingInstance, mainClassPath, matchedby="location")
                            if successLoc == True:
                                locationBasedCount = locationBasedCount + 1
                                endTime = time.time()
                                locationBasedTotalTime = locationBasedTotalTime + endTime - startTime

            else:
                if utils.getDiffType(d) == "A" or utils.getDiffType(d) == "D":
                    pass
                else:
                    locMatchingInstance = findLocBasedMatchingAlarms(paRefactoring, untrackedChild, edits)

                    if len(locMatchingInstance) > 0:
                        successLoc = recordSuccessMatch(pa, locMatchingInstance, mainClassPath, matchedby="location")
                        if successLoc == True:
                            locationBasedCount = locationBasedCount + 1
                            endTime = time.time()
                            locationBasedTotalTime = locationBasedTotalTime + endTime - startTime

            ###2.snippet-based refactoring matching.

            
            if not successLoc:
                candidates = set()
                snippetMatchingInstance = set()
                untrackedChild = childBuginstances - childTracked
                if isRefactoring:
                    for ch in untrackedChild:
                        if utils.isSameButDiffLoc(paRefactoring, ch):
                            candidates.add(ch)

                    if len(candidates) > 0:
                        if sourceCodePath in sourceChildDic:
                            parentSnippet = utils.getLineRange(sourceChildDic[sourceCodePath],
                                                            paRefactoring.getStartLine(), paRefactoring.getEndLine())
                            parentSnippet = parentSnippet.replace(" ", "")
                            for ch in candidates:
                                if utils.getDiffType(d) == "A":
                                    ###"child class path is deleted in diff"
                                    dNew = diffMap[ch.getSourcePath().replace("/", ".")]
                                    childSnippet = utils.getLineRange(sourceChildDic[dNew.a_path],
                                                                    ch.getStartLine(), ch.getEndLine())
                                    childSnippet = childSnippet.replace(" ", "")
                                else:
                                    childSnippet = utils.getLineRange(sourceChildDic[d.a_path],
                                                                    ch.getStartLine(), ch.getEndLine())
                                    childSnippet = childSnippet.replace(" ", "")
                                if childSnippet == parentSnippet:
                                    snippetMatchingInstance.add(ch)


                    else:
                        ##non-refactoring snippet matching in case cannot find snippet from parefactoring
                        parentSnippet = utils.getLineRange(sourceParentDic[d.b_path],
                                                            pa.getStartLine(), pa.getEndLine())
                        parentSnippet = parentSnippet.replace(" ", "")
            
                        
                        for ch in untrackedChild:
                            if utils.isSameButDiffLoc(pa, ch):
                                candidates.add(ch)

                        for ch in candidates:
                            if utils.getDiffType(d) == "A":
                                ###"child class path is deleted in diff"
                                dNew = diffMap[ch.getSourcePath().replace("/", ".")]
                                childSnippet = utils.getLineRange(sourceChildDic[dNew.a_path],
                                                                    ch.getStartLine(), ch.getEndLine())
                                childSnippet = childSnippet.replace(" ", "")
                            else:
                                childSnippet = utils.getLineRange(sourceChildDic[d.a_path],
                                                                    ch.getStartLine(), ch.getEndLine())
                                childSnippet = childSnippet.replace(" ", "")
                            if childSnippet == parentSnippet:
                                snippetMatchingInstance.add(ch)

                #if not isRefactoring or len(snippetMatchingInstance) == 0:
                else:
                    if utils.getDiffType(d) == "A" or utils.getDiffType(d) == "D":
                        pass
                    else:
                        candidates = set()
                        for ch in untrackedChild:
                            # if utils.isSameTypeAlarm(pa, ch):
                            ### modified:12.22
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
                    successSnippet = recordSuccessMatch(pa, snippetMatchingInstance, mainClassPath, matchedby = "snippet")
                    if successSnippet == True:
                        snippetBasedCount = snippetBasedCount + 1
                        endTime = time.time()
                        snippetBasedTotalTime = snippetBasedTotalTime + endTime - startTime
                else:
                    successSnippet = False

                # print(f"finish {count}/{len(untrackedParent)}")
                count += 1
                successAny = successSnippet
                if not successAny:

                    if mainClassPath in diffMap.keys():
                        diff = diffMap[mainClassPath]
                        if utils.getDiffType(diff) == 'D':
                            report = "disappeared"
                        else:
                            report = "fixed"
                    else:
                        report = "unknown"


                #parentTracked.add(pa)
                unmatchedParent.add(pa)
                unmatched_count +=1
                # print("the number of trackedParent", len(parentTracked))
                # print("the number of trackedChild", len(childTracked))
    untrackedChild = childBuginstances - childTracked
    untrackedParent = parentBuginstances - parentTracked

    return untrackedChild, untrackedParent,matchedPairs


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



def findLocBasedRefactoringMatchingAlarms(paRefactoring, childBuginstances):
    matchedChild = set()
    for ch in childBuginstances:
        if utils.isSameButDiffLoc(paRefactoring,ch) and abs(int(paRefactoring.getStartLine()) - int(ch.getStartLine())) <=MATCHING_THRESHOLD:
            matchedChild.add(ch)

    return matchedChild


def findLocBasedMatchingAlarms(pa, childBuginstances, edits):
    candidate1 = set(filter(lambda ch:utils.isSameButDiffLoc(pa,ch), childBuginstances))
    matchingEdits = utils.getOverlappingEditsParent(pa.getStartLine(),pa.getEndLine(), edits)
    candidate2 = set(filter(lambda ch:utils.hasEditedChild(ch.getStartLine(), ch.getEndLine(), matchingEdits), candidate1))
    matchingChild = set()

    for i in candidate2:
        if lessThanMATCHING_THRESHOLD(i, matchingEdits , pa):
            matchingChild.add(i)
    return matchingChild


if __name__ == "__main__":
    kafkaGithub = "https://github.com/apache/kafka"
    jcloudsGithub = "https://github.com/jclouds/jclouds"
    guavaGithub = "https://github.com/google/guava"
    springbootGithub = "https://github.com/spring-projects/spring-boot"

    reportsPath = r"/home/junjie/Desktop/tracking_static/data_11_6/required_reports/kafka_Spotbugs"
    saveResultsPath = r"/home/junjie/Desktop/tracking_static/data_11_6/tmp/9"
    repoPath = r"/home/junjie/Desktop/tracking_static/data_11_6/repos/kafka"
    githubPath = kafkaGithub

    PMD = xmlreader.PMDReader
    Spotbugs = xmlreader.SpotbugsReader

    parentCommits = ["4a5cba87bcd4621b999f7290d17d88d6859afb84"]
    childCommits = ["05ba5aa00847b18b74369a821e972bbba9f155eb"]


        ##start JVM
    jarpath = os.path.join(os.path.abspath('.'),
                           r'/home/junjie/Desktop/tracking_static/FixPatternMining_latest/refactoringJava/out/production/refactoringJava')
    dependency = os.path.join(os.path.abspath('.'),
                              r'/home/junjie/Desktop/tracking_static/FixPatternMining_latest/RefactoringMiner/RefactoringMiner-2.0.2/lib')

    # jarpath = os.path.join(os.path.abspath('.'),
    #                        r'/Users/lijunjie/Desktop/Git/FixPatternMining/master/FixPatternMining/refactoringJava/out/production/refactoringJava')
    # dependency = os.path.join(os.path.abspath('.'),
    #                           r'/Users/lijunjie/Desktop/Master/AnalysisTools/RefactoringMiner/build/distributions/RefactoringMiner-2.0.2/lib')

    jvmPath = jpype.getDefaultJVMPath()
    if not jpype.isJVMStarted():
        jpype.startJVM(jvmPath, "-ea", "-Djava.class.path=%s" % jarpath, "-Djava.ext.dirs=%s" % dependency)

    jClass = jpype.JClass("edu.concordia.junjie.RefactoringInfo")


    for i in range(len(parentCommits)):
        utils.checkout(repoPath, childCommits[i])
        # parentFilename = filenameOnLinux + parentCommit+'.xml'
        # childFilename = filenameOnLinux + childCommit+'.xml'

        parentFilename = os.path.join(reportsPath, parentCommits[i][0:7] + '.xml')  ##CHANGED
        childFilename = os.path.join(reportsPath  , childCommits[i][0:7] + '.xml')  ##CHANGED

        parentBuginstances = xmlreader.SpotbugsReader(parentFilename)
        childBuginstances = xmlreader.SpotbugsReader(childFilename)

        # parentBuginstances = xmlreader.SpotbugsReader(parentFilename)
        # childBuginstances = xmlreader.SpotbugsReader(childFilename)

        matchingStartTime = time.time()
        unmatchedChild, unmatchedParent,matchedPairs = matchChildParent(repoPath, parentBuginstances, childBuginstances,
                                                           parentCommits[i], childCommits[i], githubPath, jClass)


        matchingEndTime = time.time()
        print(f"commit:{childCommits[i]}")
        totoalViolationCount = len(parentBuginstances)
        print("SPOT totoalViolationCount:", totoalViolationCount)
        print("SPOT totalMatchingTime: ", matchingEndTime - matchingStartTime)
        print(f"parent warnings:{len(parentBuginstances)}\nchild warnings:{len(childBuginstances)}")
        print(f"unmatchd parent warnings:{len(unmatchedParent)}")
        print(f"unmatchd child warnings:{len(unmatchedChild)}")
    #
        print("unchangedExactMatchCount: ",unchangedExactMatchCount)
    # print("unchangedExactMatchTotalTime: ",unchangedExactMatchTotalTime)
    #
    #
        print("changedExactMatchCount: ", changedExactMatchCount)
    # print("changedExactMatchTotalTime: ", changedExactMatchTotalTime)
    #   
        print("locationBasedCount: ", locationBasedCount)
    # print("locationBasedTotalTime: ", locationBasedTotalTime)
    #
        print("snippetBasedCount: ", snippetBasedCount)
    # print("snippetBasedTotalTime: ", snippetBasedTotalTime)
    #
        print("hashBasedCount: ", hashBasedCount)
        utils.writeToGoneNew(unmatchedParent, unmatchedChild, parentCommits[i], childCommits[i], saveResultsPath,
                             saveResultsPath)
        utils.writeCSV(changed_exact_match_list,saveResultsPath)
        matchedPairsSavePath = os.path.join(saveResultsPath, str(childCommits[i]) + '.xml')
        MatchedPairsCollector.wrtieToXML(matchedPairs, matchedPairsSavePath)





    
    # shutdown JVM
    jpype.shutdownJVM() 