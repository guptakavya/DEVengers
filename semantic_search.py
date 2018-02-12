from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.corpus import wordnet as wordNet
import pysolr
import nltk
import syntactic_search
import os
from nltk.parse.stanford import StanfordDependencyParser

java_path = "C:\Program Files (x86)\\Java\\jre1.8.0_151\\bin"
os.environ['JAVAHOME'] = java_path
stanfordDepParser = StanfordDependencyParser("stanford-parser-full-2015-01-30\\stanford-parser.jar",
                                             "stanford-parser-full-2015-01-30\\stanford-parser-3.5.1-models.jar")

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
    for word in wordList:
        lemmaList.append(WordNetLemmatizer().lemmatize(word))
        stemList.append(PorterStemmer().stem(word))
        synSetList = wordNet.synsets(word)
        if len(synSetList) != 0:
            selectedWordSynSet = synSetList[0]
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
        else:
            hypernymList.append("")
            hyponymList.append("")
            meronymList.append("")
            holonymList.append("")
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
    return featureList


def getSolrSearchString(word_list):
    str = '('
    for wrd in word_list:
        str = str + '"' + wrd + '" '
    return str + ')'


if __name__ == "__main__":
    solr = pysolr.Solr('http://localhost:8983/solr/semanticCore/')
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
            articleDictionaryList.append(sentenceDictionary)
        solr.add(articleDictionaryList)

    query = raw_input("Enter query\n")
    query_words = word_tokenize(query)
    querySearchString = getSolrSearchString(query_words)

    featuresForQuery = GetFeatures(query)
    lemmaSearchString = getSolrSearchString(featuresForQuery[0])
    stemSearchString = getSolrSearchString(featuresForQuery[1])
    posSearchString = getSolrSearchString(featuresForQuery[2])
    headWordString = featuresForQuery[3]
    hypernymsSearchString = getSolrSearchString(featuresForQuery[4])
    hyponymsSearchString = getSolrSearchString(featuresForQuery[5])
    meronymsSearchString = getSolrSearchString(featuresForQuery[6])
    holonymsSearchString = getSolrSearchString(featuresForQuery[7])
    searchString = 'Words:' + querySearchString + ' Lemmas:' + lemmaSearchString + ' Stems:' + stemSearchString + ' POS:' + posSearchString + ' HeadWord:' + headWordString + ' Hypernyms:' + hypernymsSearchString + ' Hyponyms:' + hyponymsSearchString + ' Meronyms:' + meronymsSearchString + ' Holonyms:' + holonymsSearchString
    results = solr.search(q=searchString,start=0,rows=20)
    print results
