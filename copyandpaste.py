import subprocess
import pyperclip
import time
from collections import Counter, defaultdict
import liblo
import json
import random
import itertools
import argparse

copy, paste = pyperclip.determine_clipboard()

def waitForNewPaste(primary=False,timeout=None):
    """This function call blocks until a new text string exists on the
    clipboard that is different from the text that was there when the function
    was first called. It returns this text.
    This function raises PyperclipTimeoutException if timeout was set to
    a number of seconds that has elapsed without non-empty text being put on
    the clipboard."""
    """Stolen from:
    Pyperclip
    A cross-platform clipboard module for Python, with copy & paste functions for plain text.
    By Al Sweigart al@inventwithpython.com
    BSD License
    """
    startTime = time.time()
    originalText = paste(primary=primary)
    while True:
        currentText = paste(primary=primary)
        if currentText != originalText:
            return currentText
        time.sleep(0.01)
        if timeout is not None and time.time() > startTime + timeout:
            raise PyperclipTimeoutException('waitForNewPaste() timed out after ' + str(timeout) + ' seconds.')

def pastes(primary=False):
    while True:
        yield(waitForNewPaste(primary=primary))

def espeakit(text):
    p = subprocess.Popen(['./texspeak'],
                         stdin=subprocess.PIPE, close_fds=True)
    p.communicate(input=text.encode('utf-8'))


from nltk.lm import KneserNeyInterpolated
from nltk.lm.preprocessing import padded_everygram_pipeline, padded_everygrams
from nltk.tokenize import word_tokenize


# I think this is messed up
class KNLM:
    def __init__(self,n=4):
        self.n = n
        self.model = KneserNeyInterpolated(n)

    def tokenize(self, text):
        return word_tokenize(text)
    def grams_of_tokens(self, tokens):
        return padded_everygrams(self.n, tokens)
    def grams_of_text(self,text):
        return self.grams_of_tokens(self.tokenize(text))        
    def add_text(self,text):
        tokens = self.tokenize(text)
        train_data, vocab = padded_everygram_pipeline(self.n, [tokens])
        model = self.model
        if model.vocab:
            model.vocab.update(vocab)
        model.fit(train_data, vocab)
        print(f"total vocab: {len(model.vocab)}")
    def entropy(self, text):
        if len(self.model.vocab) == 0:
            return 1e100
        grams = self.grams_of_text(text)
        return self.model.entropy(grams)
        
lm = KNLM()    

class OscSetter:
    def __init__(self,host="127.0.0.1", port=57120 ):
        self.target = liblo.Address( host, port)
        self.port = port
        self.host = host
    def send(self,path,*args):
        liblo.send(self.target, path, *args)

alphabet = "abcdefghijklmnopqrstuvwxyz0123456789 "
def load_clusterfile(filename="reduce.json"):
    cluster_data = json.load(open(filename))
    reverse_index = defaultdict(list)
    for elm in cluster_data["data"]:
        reverse_index[elm.get("cluster",0)].append(elm)
    clusters = list(reverse_index.keys())
    return (cluster_data, reverse_index, clusters)

def osc_of_cluster(item):
    (path, time) = eval(item["name"])
    return [path,time,item["cluster"],item["x"],item["y"],item["z"]]

class CharMapper:
    def __init__(self,cluster_load=None,alphabet=alphabet,n=3,clusterfile="reduce.json"):
        self.alphabet = alphabet
        if cluster_load is None:
            cluster_load = load_clusterfile(clusterfile)
        self.cluster_data = cluster_load[0]
        self.reverse = cluster_load[1]
        self.clusters = cluster_load[2]
        self.mapping = defaultdict(lambda: 0)
        self.n = n
        self.alphabetset = set(self.alphabet)
    def choose_from_cluster(self, cluster):
        if not cluster in self.reverse:
            return None
        return random.choice(self.reverse[cluster])
    def choose_cluster(self):
        return random.choice(self.clusters)
    def randomize_mapping(self):
        for mapping in itertools.product(self.alphabet,repeat=self.n):
            key = "".join(mapping)
            self.mapping[key] = self.choose_cluster()
    def linear_mapping(self):
        i = 0
        for mapping in itertools.product(self.alphabet,repeat=self.n):
            key = "".join(mapping)
            v = self.clusters[i % len(self.clusters)]
            # print(f'[{key}] {v}')
            self.mapping[key] = v
            i += 1
    def choose_from_mapping(self,text):
        n = self.n
        key = [c for c in text.lower() if c in self.alphabetset][-n:]
        key = "".join(key)
        if key in self.mapping:
            return self.choose_from_cluster(self.mapping[key])
        return None        
    def get_mappings_of_text(self, text):
        n = self.n
        return [self.choose_from_mapping(text[:i+n]) for i in range(0,len(text)-n+1)]
    
def char_mapper_test():
    cm = CharMapper()
    cm.linear_mapping()
    print(cm.choose_from_mapping("aaa"))

def knlm_test():
    lm = KNLM() 
    texts = ["i like dogs", "i like cats", "i like dogs and i like cats", "this is surprising", "i like surprising cats and hogs"]
    for text in texts:
        before_e = lm.entropy(text)
        before_v = len(lm.model.vocab)
        lm.add_text(text)
        after_e = lm.entropy(text)
        after_v = len(lm.model.vocab)
        print(f'{text} {before_e} {after_e} {before_v} {after_v}')
        assert before_e > after_e
        assert before_v < after_v
        

    
def parse_args():
    parser = argparse.ArgumentParser(description=f'CopyAndPaste')
    parser.add_argument('--test', action="store_true", help='Run Tests')
    return parser.parse_args()

def run_tests():
    char_mapper_test()
    knlm_test()
    
    
def named_element_to_tuple(named_elm):
    if named_elm is None:
        return ('',0)
    if not "name" in named_elm:
        return ('',0)
    return eval(named_elm["name"])
    
def send_mappings(mappings, osc):
    if mappings is None:
        # print('mappings was None')
        return
    mc = [named_element_to_tuple(mapping) for mapping in mappings]
    # flatten
    mc = [elm for m in mc for elm in m]
    # print(f'mc:{mc}')
    osc.send( "/mappingchain", *mc)
    
def main():
    args = parse_args()
    if args.test:
        run_tests()
        return
    osc = OscSetter()
    cm = CharMapper()
    cm.randomize_mapping()
    for text in pastes(primary=True):
        print(text)
        espeakit(text)
        osc.send( "/text",  text )
        score = lm.entropy(text)
        osc.send( "/entropy", score)
        # print(f'Score: {score}')
        lm.add_text(text)
        c = Counter( text )
        alphabet = [c.get(i,0) for i in "abcdefghijklmnopqrstuvwxyz "]
        osc.send( "/alphabet", *alphabet )
        mappings = cm.get_mappings_of_text( text[-24:] )
        send_mappings(mappings, osc)
        #print(mappings)

if __name__ == "__main__":
    main()
