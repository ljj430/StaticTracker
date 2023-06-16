from xml.dom.minidom import Document

### set format and save as a xml file
def wrtieToXML(matchedPairs,filename):
    ###create dom
    doc = Document()
    ###create node
    matchedPairsList = doc.createElement('MatchedPairsList')
    doc.appendChild(matchedPairsList)
    for i in range(len(matchedPairs)):
        matchedPair = doc.createElement('MatchedPair')

        num = doc.createElement('Number')
        num_text = doc.createTextNode(str(i))
        num.appendChild(num_text)
        matchedPair.appendChild(num)

        pa = doc.createElement('ParentWarning')

        paBugDescription = doc.createElement('BugDescription')
        paBugDescription_text = doc.createTextNode(matchedPairs[i][0].getBugAbbv())
        paBugDescription.appendChild(paBugDescription_text)

        paClass = doc.createElement('Class')
        paClass_text = doc.createTextNode(matchedPairs[i][0].getClass())
        paClass.appendChild(paClass_text)

        paMethod = doc.createElement('Method')
        paMethod_text = doc.createTextNode(matchedPairs[i][0].getMethod())
        paMethod.appendChild(paMethod_text)

        paField = doc.createElement('Field')
        paField_text = doc.createTextNode(matchedPairs[i][0].getField())
        paField.appendChild(paField_text)

        paSourcePath = doc.createElement('SourcePath')
        paSourcePath_text = doc.createTextNode(matchedPairs[i][0].getSourcePath())
        paSourcePath.appendChild(paSourcePath_text)

        paStart = doc.createElement('Start')
        paStart_text = doc.createTextNode(matchedPairs[i][0].getStartLine())
        paStart.appendChild(paStart_text)

        paEnd = doc.createElement('End')
        paEnd_text = doc.createTextNode(matchedPairs[i][0].getEndLine())
        paEnd.appendChild(paEnd_text)



        pa.appendChild(paBugDescription)
        pa.appendChild(paClass)
        pa.appendChild(paMethod)
        pa.appendChild(paField)
        pa.appendChild(paSourcePath)
        pa.appendChild(paStart)
        pa.appendChild(paEnd)



        ch = doc.createElement('ChildWarning')

        chBugDescription = doc.createElement('BugDescription')
        chBugDescription_text = doc.createTextNode(matchedPairs[i][1].getBugAbbv())
        chBugDescription.appendChild(chBugDescription_text)

        chClass = doc.createElement('Class')
        chClass_text = doc.createTextNode(matchedPairs[i][1].getClass())
        chClass.appendChild(chClass_text)

        chMethod = doc.createElement('Method')
        chMethod_text = doc.createTextNode(matchedPairs[i][1].getMethod())
        chMethod.appendChild(chMethod_text)

        chField = doc.createElement('Field')
        chField_text = doc.createTextNode(matchedPairs[i][1].getField())
        chField.appendChild(chField_text)

        chSourcePath = doc.createElement('SourcePath')
        chSourcePath_text = doc.createTextNode(matchedPairs[i][1].getSourcePath())
        chSourcePath.appendChild(chSourcePath_text)

        chStart = doc.createElement('Start')
        chStart_text = doc.createTextNode(matchedPairs[i][1].getStartLine())
        chStart.appendChild(chStart_text)

        chEnd = doc.createElement('End')
        chEnd_text = doc.createTextNode(matchedPairs[i][1].getEndLine())
        chEnd.appendChild(chEnd_text)

        ch.appendChild(chBugDescription)
        ch.appendChild(chClass)
        ch.appendChild(chMethod)
        ch.appendChild(chField)
        ch.appendChild(chSourcePath)
        ch.appendChild(chStart)
        ch.appendChild(chEnd)

        matchedPair.appendChild(pa)
        matchedPair.appendChild(ch)

        matchedPairsList.appendChild(matchedPair)
    with open(filename,'wb') as f:
        f.write(doc.toprettyxml(indent='\t', encoding='utf-8'))
    return