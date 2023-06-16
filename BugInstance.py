class BugInstance:
    def __init__(self):
        self.className=""
        self.methodName=""
        self.field=""
        self.sourceStartLine="-1"
        self.sourceEndLine="-1"
        self.categoryAbbrev=""
        self.bugAbbv=""
        self.priority="-1"
        self.sourcePath=""
        self.isRefactoring = False

    def __eq__(self, other):
        if isinstance(other, BugInstance):
            return ((self.className == other.className)
                    and (self.methodName == other.methodName)
                    and (self.sourcePath == other.sourcePath)
                    and (self.bugAbbv == other.bugAbbv)
                    and (self.field == other.field)
                    and (self.sourceStartLine == other.sourceStartLine)
                    and (self.sourceEndLine == other.sourceEndLine))

        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    def __hash__(self):
        return hash(self.className) + hash(self.methodName) + hash(self.field) + hash(self.sourcePath) + hash(self.bugAbbv) + hash(self.sourceStartLine) + hash(self.sourceEndLine)

    def __str__(self):
        return "BugInstance:\n" + "Bug:" + self.bugAbbv + "\n" + "Class:" + self.className + "\n" + "Method:" + self.methodName + "\n" +"Field:" + self.field + "\n" + "SourcePath:" + self.sourcePath + "\n" \
    + "start:\n" + self.sourceStartLine + "\nend:\n" + self.sourceEndLine

    def setClass(self,className):
        self.className=className
    def setMethod(self,methodName):
        self.methodName=methodName
    def setField(self,field):
        self.field=field
    def setStartLine(self,startLine):
        self.sourceStartLine=startLine
    def setEndLine(self,endLine):
        self.sourceEndLine=endLine
    def setCategoryAbbrev(self,categoryAbbrev):
        self.categoryAbbrev=categoryAbbrev
    def setBugAbbv(self,bugAbbv):
        self.bugAbbv=bugAbbv
    def setPriority(self,priority):
        self.priority=priority
    def setSourcePath(self,sourcePath):
        self.sourcePath=sourcePath
    def setIsRefactoring(self,isRefactoring):
        self.isRefactoring = isRefactoring

    def getClass(self):
        return str(self.className)
    def getMethod(self):
        return str(self.methodName)
    def getField(self):
        return str(self.field)
    def getStartLine(self):
        return str(self.sourceStartLine)
    def getEndLine(self):
        return str(self.sourceEndLine)
    def getCategoryAbbrev(self):
        return str(self.categoryAbbrev)
    def getBugAbbv(self):
        return str(self.bugAbbv)
    def getPriority(self):
        return str(self.priority)
    def getSourcePath(self):
        return str(self.sourcePath)
