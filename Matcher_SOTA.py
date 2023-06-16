import XMLreader as xmlreader
from Utils import Diff
import Utils_exp as utils
import time
import pandas as pd
from io import StringIO
import git
from BugInstance import BugInstance
import MatchedPairsCollector
import csv
import os

MATCHING_THRESHOLD = 20
DEBUG = False
TRACK = False
trackBuginstance=BugInstance()


###set tracked buginstance
###set tracked buginstance
trackBuginstance.setBugAbbv('BeanMembersShouldSerialize')
trackBuginstance.setCategoryAbbrev('Error Prone')
trackBuginstance.setPriority('3')
trackBuginstance.setSourcePath('org/jclouds/profitbricks/http/parser/state/GetProvisioningStateResponseHandlerTest.java')
trackBuginstance.setClass('GetProvisioningStateResponseHandlerTest$GetProvisioningStateResponseHandlerTest')
trackBuginstance.setField('sampleResponses')
trackBuginstance.setStartLine('51')
trackBuginstance.setEndLine('51')


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





def matchChildParent(repoPath,parentBuginstances,childBuginstances, parentCommit,childCommit):
    global DEBUG
    global TRACK
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
    utils.checkout(repoPath,childCommit)
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
        utils.transformFilesToPackagePaths(diff,parentCommit,childCommit,repoPath)
    diffPaths = []
    for path in parentChangedPaths:
        # print(diffMap[path].b_path)
        # print(diffMap)
        if diffMap[path].b_path is None:
            continue
        diffPaths.append(diffMap[path].b_path)
    sourceParentDic = utils.getAllSourceText(repoPath, diffPaths, parentCommit)

    diffPaths = []
    for path in childChangedPaths:
        # print(diffMap[path].a_path)
        if diffMap[path].a_path is None:
            continue
        diffPaths.append(diffMap[path].a_path)
    sourceChildDic = utils.getAllSourceText(repoPath, diffPaths, childCommit)
    #mapParentPath = utils.createMapPath(kafkaPath, parentCommit)
    #mapchildPath = utils.createMapPath(kafkaPath, childCommit)
    ###inline functions
    def recordSuccessMatch(pa,matchedBugInstances, mainClassName, matchedby):
        untrackedInstances = matchedBugInstances - childTracked
        if len(untrackedInstances) == 0:
            return False
        else:
            ### check out whether it is already in tracked alarms.(if it is, exceptional case.)
            if len(untrackedInstances) != len(matchedBugInstances):
                a=1
                #print()
                #print("Some already matched!" + matchedby)
                #print("Some already matched! \n"+ pa.getClass() + " is in a changed source: " + mainClassName)
            matchedChild = list(untrackedInstances)[0]  #assuming there are one single match.
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
        mainClassPath = mainClassPath.replace("/", ".")#####kafka.api.xxx
        isChanged = False
        for path in parentChangedPaths:
            if mainClassPath in path:
                isChanged = True
        if  not isChanged: ###if not in changed  ##mainClassPath is like kafka.common.xxx.java
            ###
            ### 1.Try to find matching bugInstance in child alarm set
            ### (only one method available since it is in the unchanged set).
            ### exact matching in non-changed set.
            ###
            #print("start to match changed file")
            successAny = findExactMatching(pa,mainClassPath)
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
            else:
                successExact = False
            if not successExact:
                ###
                ### 3.Location-based matching.
                ###
                #print("start location matching")
                d = diffMap[mainClassPath]
                edits = utils.getEditList(d)
                locMatchingInstance = findLocBasedMatchingAlarms(pa, childBuginstances, edits)
                if len(locMatchingInstance) > 0:
                    successLoc = recordSuccessMatch(pa, locMatchingInstance, mainClassPath, matchedby="location")
                    if successLoc == True:
                        locationBasedCount = locationBasedCount + 1
                        endTime = time.time()
                        locationBasedTotalTime = locationBasedTotalTime + endTime - startTime
                else:
                    successLoc = False
            else:
                successLoc = True

            if not successLoc:
                ### 4. snippet-based matching: in case of moving
                d = diffMap[mainClassPath]
                if utils.getDiffType(d) == "D":
                    successSnippet = False
                else:

                    #print("start to snippet match:")
                    #snippetStartTime = time.time()
                    #print("pa instance:",pa)
                    #edits = utils.getEditList(d)
                    #parentMatchingEdits = utils.getOverlappingEditsParent(pa.getStartLine(),pa.getEndLine(),edits)

                    parentSnippet = utils.getLineRange(sourceParentDic[d.b_path],pa.getStartLine(),pa.getEndLine())
                    candidates =set()
                    for ch in childBuginstances:
                        if utils.isSameButDiffLocWithoutProcess(pa,ch):##changed
                            candidates.add(ch)
                    #if DEBUG and TRACK:
                        #print("In snippet approach\ncandidates1:\n",candidates)
                    #print("the length of candidates:", len(candidates))
                    snippetMatchingInstance = set()
                    #snippetFilterTime = time.time()
                    #print("time consumption ofcandidate filter:",snippetFilterTime-snippetStartTime)
                    if True:
                        for ch in candidates:
                            childSnippet = utils.getLineRange(sourceChildDic[d.a_path],ch.getStartLine(),ch.getEndLine())

                            if childSnippet == parentSnippet:
                                snippetMatchingInstance.add(ch)
                                successSnippet = True
                            else:
                                successSnippet = False

                    #####
                    # if len(parentMatchingEdits) > 0:
                    #     #print("parentMatchingEdits>0")
                    #     snippetMatchingInstance = set()
                    #     for ch in candidates:
                    #         childMatchingEdits = utils.getOverlappingEditsChild(ch.getStartLine(),ch.getEndLine(),parentMatchingEdits)
                    #         if len(childMatchingEdits) > 0:
                    #             childSnippet = utils.getLineRange(utils.getSourceText(repoPath,d.b_path,childCommit),ch.getStartLine(),ch.getEndLine())
                    #             if childSnippet == parentSnippet:
                    #                 snippetMatchingInstance.add(ch)
                    #                 successSnippet = True
                    #             else:
                    #                 successSnippet = False
                        #matchingTime = time.time()
                        #print("matchingTime:", matchingTime - snippetFilterTime)
                        if len(snippetMatchingInstance) > 0 :

                            successSnippet = recordSuccessMatch(pa, snippetMatchingInstance, mainClassPath, matchedby = "snippet")
                            if successSnippet == True:
                                snippetBasedCount = snippetBasedCount + 1
                                endTime = time.time()
                                snippetBasedTotalTime = snippetBasedTotalTime + endTime - startTime
                        else:
                            successSnippet = False
            else:
                successSnippet = True

            if not successSnippet:
                #### 5. hash-based matching
                d = diffMap[mainClassPath]
                if utils.getDiffType(d) == 'D':
                    successHash = False
                elif d.a_path is None:
                    successHash = False
                else:
                    parentSnippet = utils.getLineRange(sourceParentDic[d.b_path], pa.getStartLine(),pa.getEndLine())
                    candidates = set()
                    for ch in childBuginstances:
                        if utils.isSameTypeAlarm(pa,ch):
                            candidates.add(ch)

                    childSource = sourceChildDic[d.a_path]
                    parentTokens = parentSnippet.split()
                    if len(parentTokens)<= utils.HASH_SIZE:
                        successHash = False
                    else:
                        parentHeadHash = utils.hashFirstTokens(utils.HASH_SIZE, parentTokens)
                        parentTailHash = utils.hashLastTokens(utils.HASH_SIZE, parentTokens)
                        hashMatchingInstance = set()
                        for ca in candidates:
                            childSnippet = utils.getLineRange(childSource,ch.getStartLine(),ch.getEndLine())
                            childTokens = childSnippet.split()
                            childHeadHash = utils.hashFirstTokens(utils.HASH_SIZE, childTokens)
                            childTailHash = utils.hashLastTokens(utils.HASH_SIZE, childTokens)
                            if parentHeadHash == childHeadHash or parentTailHash == childTailHash:

                                hashMatchingInstance.add(ca)
                        if len(hashMatchingInstance) >0:
                            #print("hash-based matching\n")
                            #print("hash-base instance:", pa)
                            successHash = recordSuccessMatch(pa,hashMatchingInstance,mainClassPath,matchedby = "hash")
                            if successHash == True:
                                hashBasedCount = hashBasedCount + 1
                                endTime = time.time()
                                hashBasedTotalTime = hashBasedTotalTime + endTime - startTime
                        else :

                            successHash = False
            else:
                successHash = True
            successAny = successHash
        if not successAny:
            if DEBUG and TRACK:
                print("this violation is unmatched")
            unmatchedCount = unmatchedCount + 1
            endTime = time.time()
            unmatchedTotalTime = unmatchedTotalTime + endTime - startTime

            if mainClassPath in diffMap.keys():
                diff = diffMap[mainClassPath]
                if utils.getDiffType(diff) == 'D':
                    report = "disappeared"
                else:
                    report = "fixed"
            else:
                report = "unknown"
            ###print unmatched
            if DEBUG and TRACK:
                print("\nunmatched:")
                print(pa)
                print('Report:'+report+'\n')


            #parentTracked.add(pa)
            unmatchedParent.add(pa)
    time.sleep(0.01)
    untrackedChild = childBuginstances - childTracked
    untrackedParent = parentBuginstances - parentTracked
    return untrackedChild, untrackedParent,matchedPairs

def findExactMatchingAlarm(pa, childHash):
    output = []
    if pa in childHash:
        output.append(childHash[pa])
    output = set(output)
    return output

def lessThanMATCHING_THRESHOLD(x, matchingEdits , pa):
    childEdits = utils.getOverlappingEditsChild(x.getStartLine(),x.getEndLine(), matchingEdits)
    #print("childEdits:\n")
    #print(i for i in childEdits)
    for i in childEdits:
        ####
        ### check i.start_line
        ####
        #print("parent start",i.parentStart)
        #print("child start",i.childStart)
        #print("pa start",pa.getStartLine())
        #print("ch start", x.getStartLine())
        if abs(abs(int(pa.getStartLine()) - int(i.parentStart)) - abs(int(x.getStartLine()) - int(i.childStart))) <= MATCHING_THRESHOLD:
            return True
    return False

def findLocBasedMatchingAlarms(pa, childBuginstances, edits):

    candidate1 = set(filter(lambda ch:utils.isSameButDiffLocWithoutProcess(pa,ch), childBuginstances))
    matchingEdits = utils.getOverlappingEditsParent(pa.getStartLine(),pa.getEndLine(), edits)
    candidate2 = set(filter(lambda ch:utils.hasEditedChild(ch.getStartLine(), ch.getEndLine(), matchingEdits), candidate1))
    matchingChild = set()

    for i in candidate2:
        if lessThanMATCHING_THRESHOLD(i, matchingEdits , pa):
            matchingChild.add(i)
    return matchingChild

def oldMatchChildParent(repoPath,parentBuginstances,childBuginstances, parentCommit,childCommit):
    unmatchedParent =   parentBuginstances - childBuginstances
    unmatchedChild =   childBuginstances - parentBuginstances
    return unmatchedChild , unmatchedParent





if __name__ == "__main__":
    kafkaGithub = "https://github.com/apache/kafka"
    jcloudsGithub = "https://github.com/jclouds/jclouds"
    guavaGithub = "https://github.com/google/guava"
    springbootGithub = "https://github.com/spring-projects/spring-boot"

    reportsPath = r"/home/junjie/Desktop/tracking_static/data_11_6/required_reports/kafka_Spotbugs"
    saveResultsPath = r"/home/junjie/Desktop/tracking_static/data_11_6/tmp/10"
    repoPath = r"/home/junjie/Desktop/tracking_static/data_11_6/repos/kafka"
    githubPath = kafkaGithub

    PMD = xmlreader.PMDReader
    Spotbugs = xmlreader.SpotbugsReader

    parentCommits = ["4106ff6e5a61b76c5f05377df6f31fa8ae50c73b"]
    childCommits = ["0984a76b712caa18c688eafbacaa2a7c889d27b2"]



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
                                                           parentCommits[i], childCommits[i])


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
        matchedPairsSavePath = os.path.join(saveResultsPath, str(childCommits[i]) + '.xml')
        MatchedPairsCollector.wrtieToXML(matchedPairs, matchedPairsSavePath)