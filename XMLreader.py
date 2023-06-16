import xml.sax
from BugInstance import BugInstance as BugIns
import sys
import pandas as pd
import time
import os
import Utils as utils


# kafkaResult1=sys.argv[1]
# kafkaResult2=sys.argv[2]
# kafkaResult1="spotbugs_kafka_4a5cba87bcd4621b999f7290d17d88d6859afb84.xml"
# kafkaResult2="spotbugs_kafka_05ba5aa00847b18b74369a821e972bbba9f155eb.xml"
class FindbugsHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.CurrentData = ""
        self.type = ""
        self.category = ""
        self.className = ""
        self.methodName = ""
        self.start = ""
        self.end = ""
        self.sourceFile = ""
        self.sourcePath = ""
        self.bugInstanceList = []
        self.bugInstance = BugIns()
        self.priority = ""
        self.fieldName = ""
        self.isInType = False
        self.isInRoleClass = False
        self.isInRoleMethod = False
        self.isInRoleField = False

        # process beginning of elements

    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "BugInstance":
            self.bugInstance = BugIns()
            self.type = attributes["type"]
            self.bugInstance.setBugAbbv(self.type)
            self.category = attributes["category"]
            self.bugInstance.setCategoryAbbrev(self.category)
            self.priority = attributes["priority"]
            self.bugInstance.setPriority(self.priority)
            # self.bugInstanceList.append({})
        elif tag == "Class":  ###extract class information
            if "role" not in attributes.getNames():
                self.className = attributes["classname"]
                self.bugInstance.setClass(self.className)
            else :
                self.isInRoleClass = True

        elif tag == "Method":  ###extract method information
            if "role" not in attributes.getNames():
                self.methodName = attributes["name"]


                # tokens = self.methodName.split("$")
                # self.methodName = tokens[0]

                self.bugInstance.setMethod(self.methodName)
            else :
                self.isInRoleMethod = True

        elif tag == "Field":
            if "role" not in attributes.getNames():
                self.fieldName = attributes["name"]

                # tokens = self.fieldName.split("$")
                # self.fieldName = tokens[0]

                self.bugInstance.setField(self.fieldName)
            else :
                self.isInRoleField = True
        elif tag == "Type":  #####drop it
            self.isInType = True

        elif tag == "SourceLine":
            if not self.isInType and not self.isInRoleClass and not self.isInRoleMethod and not self.isInRoleField:
                if "sourcepath" in attributes.getNames():
                    self.sourcePath = attributes["sourcepath"]
                    self.bugInstance.setSourcePath(self.sourcePath)
                if "start" in attributes.getNames() and "end" in attributes.getNames() and "role" not in attributes.getNames():
                    self.start = attributes["start"]
                    self.end = attributes["end"]
                    self.bugInstance.setStartLine(self.start)
                    self.bugInstance.setEndLine(self.end)
            else:
                pass

    # process end of elements
    def endElement(self, tag):
        self.CurrentData = tag
        if self.CurrentData == "BugInstance":
            self.bugInstanceList.append(self.bugInstance)
            self.className = ''
            self.methodName = ''
            self.sourcePath = ''
            self.fieldName = ''
            self.start = ''
            self.end = ''
        elif self.CurrentData == "Type":
            self.isInType = False
        elif self.CurrentData == "Class":
            self.isInRoleClass = False
        elif self.CurrentData == "Method":
            self.isInRoleMethod = False
        elif self.CurrentData == "Field":
            self.isInRoleField = False
        self.CurrentData = ""

    # process event content
    def characters(self, content):
        # print("content",content)
        # print("CurrentData",self.CurrentData)
        if self.CurrentData == "type":
            self.type = content
        elif self.CurrentData == "category":
            self.category = content
        elif self.CurrentData == "Class":
            self.className = content





class PMDHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.CurrentData = ""
        self.type = ""
        self.category = ""
        self.className = ""
        self.methodName = ""
        self.start = ""
        self.end = ""
        self.sourceFile = ""
        self.sourcePath = ""
        self.bugInstanceList = []
        self.bugInstance = BugIns()
        self.priority = ""
        self.fieldName = ""
        self.noClassFlag =False

        # process beginning of elements

    def startElement(self, tag, attributes):
        self.CurrentData = tag
        #print(f'tag:{tag}')
        if tag == "file":

            self.sourcePath = attributes["name"]
            #tmpSoutcePaths = self.sourcePath.split(os.sep)
            if '/' in self.sourcePath:
                sep = '/'
            elif '\\' in self.sourcePath:
                sep = '\\'
                self.sourcePath = self.sourcePath.replace(sep,'/')

            self.sourcePath = utils.getClassPath(self.sourcePath)

        if tag == "violation":
            if 'class' not in attributes.getNames():
                self.noClassFlag = True
            else:
                self.noClassFlag = False

            if self.noClassFlag == False:
                self.bugInstance = BugIns()
                self.start = attributes["beginline"]
                self.end = attributes["endline"]
                #print(f'start:{self.start}')
                #print(f'end:{self.end}')
                self.bugInstance.setStartLine(self.start)
                self.bugInstance.setEndLine(self.end)
                self.type = attributes["rule"]
                self.bugInstance.setBugAbbv(self.type)
                self.category = attributes["ruleset"]
                self.bugInstance.setCategoryAbbrev(self.category)
                self.priority = attributes["priority"]
                self.bugInstance.setPriority(self.priority)
                self.className = attributes["class"]
                self.bugInstance.setClass(self.className)
                self.bugInstance.setSourcePath(self.sourcePath)
                if 'method' in attributes.getNames():
                    self.methodName = attributes["method"]
                    self.bugInstance.setMethod(self.methodName)
                if 'variable' in attributes.getNames():
                    self.fieldName = attributes["variable"]
                    self.bugInstance.setField(self.fieldName)
            # self.bugInstanceList.append({})

    # process end of elements
    def endElement(self, tag):
        self.CurrentData = tag
        if self.CurrentData == "violation" and self.noClassFlag == False:
            self.bugInstanceList.append(self.bugInstance)
            self.className = ''
            self.methodName = ''
            self.fieldName = ''
            self.start = ''
            self.end = ''
        elif self.CurrentData == "file":
            self.sourcePath = ''
        self.CurrentData = ""

    # comment due to the japan language
    # process event content
    # def characters(self, content):
    #     #print(f'type of content:{type(content)}')
    #
    #     print(f'content:{content}')
    #
    #     if self.CurrentData == "type":
    #         self.type = content
    #     elif self.CurrentData == "category":
    #         self.category = content
    #     elif self.CurrentData == "Class":
    #         self.className = content





def SpotbugsReader(filename):  ###for the new approach
    # create a XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    # rewrite the ContextHandler
    Handler = FindbugsHandler()
    parser.setContentHandler(Handler)
    parser.parse(filename)  ####June 6 2018 commits 5104
    bugInstances = Handler.bugInstanceList
    return set(bugInstances)



def PMDReader(filename):
    # create a XMLReader
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    # rewrite the ContextHandler
    Handler = PMDHandler()
    parser.setContentHandler(Handler)
    parser.parse(filename)  ####June 6 2018 commits 5104
    bugInstances = Handler.bugInstanceList
    return set(bugInstances)




###Jsut a test
if __name__ == "__main__":
    print(os.listdir('.'))

    filename = "/Users/lijunjie/Desktop/Master/Thesis/Task/Week9/5 commits/reports/2a56db0test.xml"

    buginstances = SpotbugsReader(filename)
    for b in buginstances:
        print(b)

