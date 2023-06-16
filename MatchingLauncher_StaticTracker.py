import sys
import time
import Matcher_StaticTracker as matchedImproved
import XMLreader as xmlreader
import os
import pandas as pd
import jpype
import Utils as utils
import MatchedPairsCollector
import yaml


## set your config file here.
# config_file = r"/home/junjie/Desktop/tracking_static/FixPatternMining_publish/config.yaml"
config_file = sys.argv[1]
with open(config_file, 'r') as stream:
    configs = yaml.safe_load(stream)
print(configs)

##start JVM to load RefactoringMiner

java_jar_path = configs['java_jar_path']
java_dependency_path = configs['java_dependency_path']
jarpath = os.path.join(os.path.abspath('.'),
                       java_jar_path)
dependency = os.path.join(os.path.abspath('.'),
                            java_dependency_path )

jvmPath = jpype.getDefaultJVMPath()
if not jpype.isJVMStarted():
    jpype.startJVM(jvmPath, "-ea", "-Djava.class.path=%s" % jarpath, "-Djava.ext.dirs=%s" % dependency)

jClass = jpype.JClass("edu.concordia.junjie.RefactoringInfo")

remote_repo_path = configs['remote_repo_path']
local_repo_path = configs['loc_repo_path']

parentCommit = configs['parent_commit']
childCommit = configs['child_commit']
child_report_path = configs['child_report_path']
parent_report_path = configs['parent_report_path']

saveResultsPath = configs['save_result_path']

staticTool = configs['static_tool']
if staticTool == 'Spotbugs':
    Reader = xmlreader.SpotbugsReader
elif staticTool == 'PMD':
    Reader = xmlreader.PMDReader
else:
    print(f"Unknow static tool: {staticTool}")
    exit(1)


goneResultsPath = os.path.join(saveResultsPath, 'gone')
newResultsPath = os.path.join(saveResultsPath, 'new')
if not os.path.exists(goneResultsPath):
    os.mkdir(goneResultsPath)
if not os.path.exists(newResultsPath):
    os.mkdir(newResultsPath)


###step1 read commitlist and set parent commit and child commit
print(f"stat to analyze the repo: {remote_repo_path}")
print(f"static_tool:{staticTool}\nchild commit:{childCommit}")

parentBuginstances = Reader(parent_report_path)
childBuginstances = Reader(child_report_path)

matchingStartTime = time.time()

#### Run StaticTracker
unmatchedChild, unmatchedParent,matchedPairs = matchedImproved.matchChildParent(local_repo_path, parentBuginstances, childBuginstances,
                                                        parentCommit, childCommit, remote_repo_path, jClass)
matchingEndTime = time.time()

utils.writeToGoneNew(unmatchedParent, unmatchedChild,  parentCommit[0:7], childCommit[0:7], goneResultsPath, newResultsPath)
row = [childCommit[0:7], matchingEndTime - matchingStartTime]
# utils.writeToTime(timeMeasurePath, row)
matchedPairsSavePath = os.path.join(saveResultsPath, str(childCommit[0:7]) + '_matched_pairs' + '.xml')
MatchedPairsCollector.wrtieToXML(matchedPairs, matchedPairsSavePath)
print(f"finish the matching of {staticTool}")


jpype.shutdownJVM()





