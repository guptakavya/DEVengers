from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.corpus import wordnet as wordNet
import pysolr
import nltk
import syntactic_search
import semantic_search
import os
from nltk.parse.stanford import StanfordDependencyParser

java_path = "C:\Program Files (x86)\\Java\\jre1.8.0_151\\bin"
os.environ['JAVAHOME'] = java_path
stanfordDepParser = StanfordDependencyParser(
    "stanford-parser-full-2015-01-30\\stanford-parser.jar",
    "stanford-parser-full-2015-01-30\\stanford-parser-3.5.1-models.jar")

def initialize(word):
    """
        Function to initialize the best sense and retrieve the definition and examples of each sense
    """
    bankSyns = wordNet.synsets(word)
    bestSense = bankSyns[0]
    synRelations = dict()
    maxCount = 0
    for syn in bankSyns:
        syndetails = dict()
        count = syn.lemmas()[0].count()
        syndetails["count"] = count
        syndetails["definition"] = word_tokenize(syn.definition())
        examples = syn.examples()
        egWords = []
        for example in examples:
            egWords.extend(word_tokenize(example))
        syndetails["examples"] = egWords
        synRelations[syn] = syndetails
        if count > maxCount:
           bestSense = syn
           maxCount = count
    return synRelations, bestSense

def computeOverlap(signature, context):
    """
        Function to overlap for sense
    """
    overlap = 0
    for word in context:
        for ref in signature:
            if str(word) == str(ref):
                overlap += 1
                break
    return overlap

def desk(context, synRelations, intBestSense):
    """
        Function to apply the Lesk algorithm and find the best sense
    """
    bestSense = intBestSense
    maxOverlap = 0
    overLapDict = dict()
    for sense, relations in synRelations.iteritems():
        signature = relations["definition"]
        signature.extend(relations["examples"])
        overlap = computeOverlap(signature, context)
        overLapDict[sense] = overlap
        if overlap > maxOverlap:
            maxOverlap = overlap
            bestSense = sense
    return bestSense, overLapDict


def GetFeatures(sentence):
    featureList = []
    wordList = word_tokenize(sentence)
    # Get Lemma, Stem, hypernym, hyponym,meronym,holonym for each word
    lemmaList = []
    stemList = []
    hypernymList = []
    hyponymList = []
    meronymList = []
    holonymList = []
    synonymList = []
    for word in wordList:
        lemmaList.append(WordNetLemmatizer().lemmatize(word))
        stemList.append(PorterStemmer().stem(word))
        synSetList = wordNet.synsets(word)
        if len(synSetList) != 0:
            synRelations, intBestSense = initialize(word)
            bestSense, overlap = desk(wordList, synRelations, intBestSense)
            selectedWordSynSet = bestSense
            if (len(selectedWordSynSet.hypernyms()) != 0):
                wordHypernym = selectedWordSynSet.hypernyms()[0]
                if (len(wordHypernym.lemmas()) != 0):
                    hypernymList.append(wordHypernym.lemmas()[0].name())
                else:
                    hypernymList.append("")
            else:
                hypernymList.append("")
            if (len(selectedWordSynSet.hyponyms()) != 0):
                wordHyponym = selectedWordSynSet.hyponyms()[0]
                if (len(wordHyponym.lemmas()) != 0):
                    hyponymList.append(wordHyponym.lemmas()[0].name())
                else:
                    hyponymList.append("")
            else:
                hyponymList.append("")
            if (len(selectedWordSynSet.part_meronyms()) != 0):
                wordMeronym = selectedWordSynSet.part_meronyms()[0]
                if (len(wordMeronym.lemmas()) != 0):
                    meronymList.append(wordMeronym.lemmas()[0].name())
                else:
                    meronymList.append("")
            else:
                meronymList.append("")
            if (len(selectedWordSynSet.part_holonyms()) != 0):
                wordHolonym = selectedWordSynSet.part_holonyms()[0]
                if (len(wordHolonym.lemmas()) != 0):
                    holonymList.append(wordHolonym.lemmas()[0].name())
                else:
                    holonymList.append("")
            else:
                holonymList.append("")
            if (len(selectedWordSynSet.lemmas())!=0):
                synonymList.append(selectedWordSynSet.lemmas()[0].name())
            else:
                synonymList.append("")
        else:
            hypernymList.append("")
            hyponymList.append("")
            meronymList.append("")
            holonymList.append("")
            synonymList.append("")
    featureList.append(lemmaList)
    featureList.append(stemList)
    # Get POS for each word
    taggedWordList = nltk.pos_tag(wordList)
    posList = []
    for taggedWord in taggedWordList:
        posList.append(taggedWord[1])
    featureList.append(posList)
    # Get HeadWord for the sentence
    headWord = ""
    striped_sentence = sentence.strip(" '\"")
    if len(striped_sentence) != 0:
        dependency_parser = stanfordDepParser.raw_parse(striped_sentence)
        parseTree = list(dependency_parser)[0]
        for n in parseTree.nodes.values():
            if n['head'] == 0:
                headWord = n['word']
                break
    featureList.append(headWord)
    # add hypernym,hyponym,meronym and holonym lists to feature list
    featureList.append(hypernymList)
    featureList.append(hyponymList)
    featureList.append(meronymList)
    featureList.append(holonymList)
    featureList.append(synonymList)
    return featureList


if __name__ == "__main__":
    solr = pysolr.Solr('http://localhost:8983/solr/advancedSemanticCore')
    for fileLoc in os.listdir("reuters\\training\\"):
        file = open("reuters\\training\\" + fileLoc)
        sentences = syntactic_search.SegmentArticle(file)
        articleDictionaryList = []
        for sentence in sentences:
            sentenceDictionary = {}
            wordList = word_tokenize(sentence)
            features = GetFeatures(sentence)
            sentenceDictionary['article'] = fileLoc
            sentenceDictionary['sentence'] = sentence
            sentenceDictionary['Words'] = wordList
            sentenceDictionary['Lemmas'] = features[0]
            sentenceDictionary['Stems'] = features[1]
            sentenceDictionary['POS'] = features[2]
            sentenceDictionary['HeadWord'] = features[3]
            sentenceDictionary['Hypernyms'] = features[4]
            sentenceDictionary['Hyponyms'] = features[5]
            sentenceDictionary['Meronyms'] = features[6]
            sentenceDictionary['Holonyms'] = features[7]
            sentenceDictionary['Synonyms'] = features[8]
            articleDictionaryList.append(sentenceDictionary)
        solr.add(articleDictionaryList)
    query = raw_input("Enter query\n")
    query_words = word_tokenize(query)
    querySearchString = semantic_search.getSolrSearchString(query_words)

    featuresForQuery = GetFeatures(query)
    lemmaSearchString = semantic_search.getSolrSearchString(featuresForQuery[0])
    stemSearchString = semantic_search.getSolrSearchString(featuresForQuery[1])
    posSearchString = semantic_search.getSolrSearchString(featuresForQuery[2])
    headWordString = featuresForQuery[3]
    hypernymsSearchString = semantic_search.getSolrSearchString(featuresForQuery[4])
    hyponymsSearchString = semantic_search.getSolrSearchString(featuresForQuery[5])
    meronymsSearchString = semantic_search.getSolrSearchString(featuresForQuery[6])
    holonymsSearchString = semantic_search.getSolrSearchString(featuresForQuery[7])
    synonymSearchString  = semantic_search.getSolrSearchString(featuresForQuery[8])
    searchString = 'Words:' + querySearchString + ' Lemmas:' + lemmaSearchString + ' Stems:' + stemSearchString + ' POS:' + posSearchString + ' HeadWord:' + headWordString + ' Hypernyms:' + hypernymsSearchString + ' Hyponyms:' + hyponymsSearchString + ' Meronyms:' + meronymsSearchString + ' Holonyms:' + holonymsSearchString + 'Synonyms:' +synonymSearchString
    results = solr.search(q=searchString,start=0,rows=20)
    print results