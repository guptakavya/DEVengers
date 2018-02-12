from nltk.tokenize import sent_tokenize, word_tokenize
import pysolr
import os

def SegmentArticle(article):
    text = article.read()
    sentences = sent_tokenize(text)
    return sentences

if __name__ == "__main__" :
    solr = pysolr.Solr('http://localhost:8983/solr/syntacticCore/')
    articleDictionaryList = []
    for fileLoc in os.listdir("reuters\\training\\"):
        file = open("reuters\\training\\" + fileLoc)
        sentences = SegmentArticle(file)
        for sentence in sentences:
            words = word_tokenize(sentence)
            data = {}
            data["article"] = fileLoc
            data["sentence"] = sentence
            data["wordList"] = words
            articleDictionaryList.append(data)
    solr.add(articleDictionaryList)
    query = raw_input("Enter query")
    queryWords = word_tokenize(query)
    searchString = '('
    for word in queryWords:
        searchString = searchString + '"' + word + '" '
    searchString = 'wordList:' + searchString + ')'
    results = solr.search(q=searchString, start=0, rows=20)
    print results