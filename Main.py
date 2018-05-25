import string
import sys
import numpy as np
from nltk.stem import WordNetLemmatizer

class PorterStemmer:

    def __init__(self):


        self.b = ""  # buffer for word to be stemmed
        self.k = 0
        self.k0 = 0
        self.j = 0   # j is a general offset into the string

    def cons(self, i):

        if self.b[i] == 'a' or self.b[i] == 'e' or self.b[i] == 'i' or self.b[i] == 'o' or self.b[i] == 'u':
            return 0
        if self.b[i] == 'y':
            if i == self.k0:
                return 1
            else:
                return (not self.cons(i - 1))
        return 1

    def m(self):

        n = 0
        i = self.k0
        while 1:
            if i > self.j:
                return n
            if not self.cons(i):
                break
            i = i + 1
        i = i + 1
        while 1:
            while 1:
                if i > self.j:
                    return n
                if self.cons(i):
                    break
                i = i + 1
            i = i + 1
            n = n + 1
            while 1:
                if i > self.j:
                    return n
                if not self.cons(i):
                    break
                i = i + 1
            i = i + 1

    def vowelinstem(self):
        #vowelinstem() is TRUE <=> k0,...j contains a vowel#
        for i in range(self.k0, self.j + 1):
            if not self.cons(i):
                return 1
        return 0

    def doublec(self, j):
        #doublec(j) is TRUE <=> j,(j-1) contain a double consonant.
        if j < (self.k0 + 1):
            return 0
        if (self.b[j] != self.b[j-1]):
            return 0
        return self.cons(j)

    def cvc(self, i):
        #cvc(i) is TRUE <=> i-2,i-1,i has the form consonant - vowel - consonant
        #and also if the second c is not w,x or y. this is used when trying to
        #restore an e at the end of a short  e.g.

         #  cav(e), lov(e), hop(e), crim(e), but
          # snow, box, tray.

        if i < (self.k0 + 2) or not self.cons(i) or self.cons(i-1) or not self.cons(i-2):
            return 0
        ch = self.b[i]
        if ch == 'w' or ch == 'x' or ch == 'y':
            return 0
        return 1

    def ends(self, s):
        #ends(s) is TRUE <=> k0,...k ends with the string s.
        length = len(s)
        if s[length - 1] != self.b[self.k]: # tiny speed-up
            return 0
        if length > (self.k - self.k0 + 1):
            return 0
        if self.b[self.k-length+1:self.k+1] != s:
            return 0
        self.j = self.k - length
        return 1

    def setto(self, s):
        #setto(s) sets (j+1),...k to the characters in the string s, readjusting k.
        length = len(s)
        self.b = self.b[:self.j+1] + s + self.b[self.j+length+1:]
        self.k = self.j + length

    def r(self, s):

        if self.m() > 0:
            self.setto(s)

    def step1ab(self):
        """step1ab() gets rid of plurals and -ed or -ing. e.g.

           caresses  ->  caress
           ponies    ->  poni
           ties      ->  ti
           caress    ->  caress
           cats      ->  cat

           feed      ->  feed
           agreed    ->  agree
           disabled  ->  disable

           matting   ->  mat
           mating    ->  mate
           meeting   ->  meet
           milling   ->  mill
           messing   ->  mess

           meetings  ->  meet
            """
        if self.b[self.k] == 's':
            if self.ends("sses"):
                self.k = self.k - 2
            elif self.ends("ies"):
                self.setto("i")
            elif self.b[self.k - 1] != 's':
                self.k = self.k - 1
        if self.ends("eed"):
            if self.m() > 0:
                self.k = self.k - 1
        elif (self.ends("ed") or self.ends("ing")) and self.vowelinstem():
            self.k = self.j
            if self.ends("at"):   self.setto("ate")
            elif self.ends("bl"): self.setto("ble")
            elif self.ends("iz"): self.setto("ize")
            elif self.doublec(self.k):
                self.k = self.k - 1
                ch = self.b[self.k]
                if ch == 'l' or ch == 's' or ch == 'z':
                    self.k = self.k + 1
            elif (self.m() == 1 and self.cvc(self.k)):
                self.setto("e")

    def step1c(self):
        #step1c() turns terminal y to i when there is another vowel in the stem.
        if (self.ends("y") and self.vowelinstem()):
            self.b = self.b[:self.k] + 'i' + self.b[self.k+1:]

    def step2(self):
        #step2() maps double suffices to single ones.
        #so -ization ( = -ize plus -ation) maps to -ize etc. note that the
        #string before the suffix must give m() > 0.

        if self.b[self.k - 1] == 'a':
            if self.ends("ational"):   self.r("ate")
            elif self.ends("tional"):  self.r("tion")
        elif self.b[self.k - 1] == 'c':
            if self.ends("enci"):      self.r("ence")
            elif self.ends("anci"):    self.r("ance")
        elif self.b[self.k - 1] == 'e':
            if self.ends("izer"):      self.r("ize")
        elif self.b[self.k - 1] == 'l':
            if self.ends("bli"):       self.r("ble") # --DEPARTURE--
            # To match the published algorithm, replace this phrase with
            #   if self.ends("abli"):      self.r("able")
            elif self.ends("alli"):    self.r("al")
            elif self.ends("entli"):   self.r("ent")
            elif self.ends("eli"):     self.r("e")
            elif self.ends("ousli"):   self.r("ous")
        elif self.b[self.k - 1] == 'o':
            if self.ends("ization"):   self.r("ize")
            elif self.ends("ation"):   self.r("ate")
            elif self.ends("ator"):    self.r("ate")
        elif self.b[self.k - 1] == 's':
            if self.ends("alism"):     self.r("al")
            elif self.ends("iveness"): self.r("ive")
            elif self.ends("fulness"): self.r("ful")
            elif self.ends("ousness"): self.r("ous")
        elif self.b[self.k - 1] == 't':
            if self.ends("aliti"):     self.r("al")
            elif self.ends("iviti"):   self.r("ive")
            elif self.ends("biliti"):  self.r("ble")
        elif self.b[self.k - 1] == 'g': # --DEPARTURE--
            if self.ends("logi"):      self.r("log")
        # To match the published algorithm, delete this phrase

    def step3(self):
        #step3() dels with -ic-, -full, -ness etc. similar strategy to step2.
        if self.b[self.k] == 'e':
            if self.ends("icate"):     self.r("ic")
            elif self.ends("ative"):   self.r("")
            elif self.ends("alize"):   self.r("al")
        elif self.b[self.k] == 'i':
            if self.ends("iciti"):     self.r("ic")
        elif self.b[self.k] == 'l':
            if self.ends("ical"):      self.r("ic")
            elif self.ends("ful"):     self.r("")
        elif self.b[self.k] == 's':
            if self.ends("ness"):      self.r("")

    def step4(self):

        if self.b[self.k - 1] == 'a':
            if self.ends("al"): pass
            else: return
        elif self.b[self.k - 1] == 'c':
            if self.ends("ance"): pass
            elif self.ends("ence"): pass
            else: return
        elif self.b[self.k - 1] == 'e':
            if self.ends("er"): pass
            else: return
        elif self.b[self.k - 1] == 'i':
            if self.ends("ic"): pass
            else: return
        elif self.b[self.k - 1] == 'l':
            if self.ends("able"): pass
            elif self.ends("ible"): pass
            else: return
        elif self.b[self.k - 1] == 'n':
            if self.ends("ant"): pass
            elif self.ends("ement"): pass
            elif self.ends("ment"): pass
            elif self.ends("ent"): pass
            else: return
        elif self.b[self.k - 1] == 'o':
            if self.ends("ion") and (self.b[self.j] == 's' or self.b[self.j] == 't'): pass
            elif self.ends("ou"): pass
            # takes care of -ous
            else: return
        elif self.b[self.k - 1] == 's':
            if self.ends("ism"): pass
            else: return
        elif self.b[self.k - 1] == 't':
            if self.ends("ate"): pass
            elif self.ends("iti"): pass
            else: return
        elif self.b[self.k - 1] == 'u':
            if self.ends("ous"): pass
            else: return
        elif self.b[self.k - 1] == 'v':
            if self.ends("ive"): pass
            else: return
        elif self.b[self.k - 1] == 'z':
            if self.ends("ize"): pass
            else: return
        else:
            return
        if self.m() > 1:
            self.k = self.j

    def step5(self):

        self.j = self.k
        if self.b[self.k] == 'e':
            a = self.m()
            if a > 1 or (a == 1 and not self.cvc(self.k-1)):
                self.k = self.k - 1
        if self.b[self.k] == 'l' and self.doublec(self.k) and self.m() > 1:
            self.k = self.k -1

    def stem(self, p, i, j):
        #In stem(p,i,j), p is a char pointer, and the string to be stemmed
        #is from p[i] to p[j] inclusive. Typically i is zero and j is the
        #offset to the last character of a string, (p[j+1] == '\0'). The
        #stemmer adjusts the characters p[i] ... p[j] and returns the new
        #end-point of the string, k. Stemming never increases word length, so
        #i <= k <= j. To turn the stemmer into a module, declare 'stem' as
        #extern, and delete the remainder of this file.

        # copy the parameters into statics
        self.b = p
        self.k = j
        self.k0 = i
        if self.k <= self.k0 + 1:
            return self.b # --DEPARTURE--

        # With this line, strings of length 1 or 2 don't go through the
        # stemming process, although no mention is made of this in the
        # published algorithm. Remove the line to match the published
        # algorithm.

        self.step1ab()
        self.step1c()
        self.step2()
        self.step3()
        self.step4()
        self.step5()
        return self.b[self.k0:self.k+1]

def StemmerIt (str1):
        p = PorterStemmer()
        infile = open(str1, 'r')
        outlist = []
        while 1:
            output = ''
            word = ''
            line = infile.readline()
            if line == '':
                break
            for c in line:
                if c.isalpha():
                    word += c.lower()
                else:
                    if word:
                        output += p.stem(word, 0,len(word)-1)
                        word = ''
                    output += c.lower()
            outlist.append(output),
        infile.close()
        return outlist

def RemoveDigits(str1):
    str2 = str(str1)
    result = ''.join([i for i in str2 if not i.isdigit()])
    return result

def RemovePunchuations(str1):
    str1 = str1.replace('"""','"').replace('.','').replace(',','').replace('?','').replace('!','').replace(':','').replace(';','').replace('|','').replace('+','')
    str1=str1.replace('(','').replace(')','').replace('[','').replace(']','').replace('{','').replace('}','').replace('*','')
    str1 = str1.replace("'",'').replace('£','').replace('$','').replace('/','').replace('-','').replace('€','').replace('˜','').replace('_','')
    return str1

def RemoveStopWord(str1 , stoplist):
    str1 = ' '+str1 + ' '
    for row in stoplist :
        row1 = ' '+row.strip()+' '
        if row1 in str1 :
            str1 = str1.replace(row1,' ')
    return str1

def BagOfWords(lst):
    col = set()
    baglist = []
    for line in lst :
       for row in line[1:]:col.add(row)
    #col.remove('')
    baglist.append(str(col)[1:-1].replace(" '",'').replace("'",'').split(','))


    for i,line in enumerate(lst) :
        baglist.append(str(col)[1:-1].replace(" '", '').replace("'", '').split(','))
        baglist[i+1][0] =line[0]
        for j,row in enumerate(line[1:]):
            for k,w in enumerate(baglist[0]):
                if w == row or baglist[i+1][k] == 1:
                    baglist[i+1][k] = 1
                else: baglist[i+1][k] = 0
        baglist[i+1][0 ] = line[0]

    return baglist

def NaiveBayes (trainlst1,testlst1):
    matrix = [] ; hCount = 0 ; sCount=0 ; hdict = {} ; sdict = {}
    matrix.append(trainlst1[0])
    matrix.append(np.zeros(len(trainlst1[0])))
    matrix.append(np.zeros(len(trainlst1[0])))
    for i,line in enumerate(trainlst1) :
        if i == 0 :continue
        for j,row in enumerate(line):
            if row==1 :
                if line[0]=='h' :
                    matrix[1][j] +=1  ; hCount +=1 ;
                if trainlst1[0][j] in hdict.keys():
                            hdict[trainlst1[0][j]] += 1
                else : hdict[trainlst1[0][j]] = 1

                if line[0]=='s' :
                    matrix[2][j] +=1 ; sCount +=1 ;
                if trainlst1[0][j] in sdict.keys():
                            sdict[trainlst1[0][j]] += 1
                else : sdict[trainlst1[0][j]] = 1


    ep = 0.0001
    tp = 0 ; tn = 0 ; fp = 0 ; fn = 0 ;
    for i,line in enumerate(testlst1):
        temph = 1.0;temps = 1.0
        if i == 0 :continue
        for j,row in enumerate(line):
            if testlst1[0][j] in hdict.keys():
                if row==1 :
                    temph = temph*((hdict[testlst1[0][j]]+ep)/(hCount+ hCount*ep))
                elif row == 0 :
                    temph = temph * (1-((hdict[testlst1[0][j]] + ep) / (hCount + hCount * ep)))
            if testlst1[0][j] in sdict.keys():
                if row==1 :
                    temps = temps*((sdict[testlst1[0][j]]+ep)/(sCount+ sCount*ep))
                elif row == 0 :
                    temps = temps * (1-((sdict[testlst1[0][j]] + ep) / (sCount + sCount * ep)))

        if   temps > temph  and line[0] == 'h': tp +=1
        elif temps <= temph and line[0] == 'h': fn +=1
        elif temps > temph   and line[0] == 's': tn +=1
        elif temps <= temph and line[0] == 's': fp +=1

    print((tp+tn)/(tp+tn+fp+fn))
    print('True Positive Rate = '+str(tp))
    print('True Negative Rate = '+str(tn))
    print('False Positive Rate = '+str(fp))
    print('False Negative Rate = '+str(fn))

f1 = "HW2\\stopwords.csv"
f2 = "HW2\\sms_spam.csv"
stop = open(f1,'r')
smsfile = open(f2,'r')
temp = stop.readline()
SW2 = temp.split(",")


# with stemmer
"""smslist = StemmerIt(f2)
for line in smslist:
    str1 = line.split(',')
    print(str1[1])

str2 = 'asdasda. as a we all 123  ffasd ? !a? :; swimming swims thus probs sos'
str3 = RemovePunchuations(str2)

str4 = RemoveDigits(str3)
str5 = RemoveStopWord(str4 ,SW2)
print(str2)
print(str3)
print(str4)
print(str5)
"""


spamlist = []
hamlist = []
for i,line in enumerate(smsfile) :
    if line!='"type","text"':

        str1 = RemovePunchuations(RemoveDigits(RemoveStopWord(line.lower(),SW2))).replace('"\n','').split('""')
        if str1[0].replace(' "','') == 'ham' :
            hamlist.append(str1[1].split(' '))
        else:
            spamlist.append(str(str1[1]).strip().split(' '))

hamPerc =(round(0.8*len(hamlist)));    spamPerc = (round(0.8*len(spamlist))) ;       trainList =[] ; testList = []
#fill trainList
for i,line in enumerate(hamlist):
    str1 = 'h,' + str(line).replace("'',",'').replace(", ''",'').replace("'",'').replace(' ','')[1:-1]
    if i < hamPerc :
        trainList.append(str1.split(','))
    else:
        testList.append(str1.split(','))

#fill testList
for i,line in enumerate(spamlist):
    str1 = 's,' + str(line).replace("'',",'').replace(", ''",'').replace("'",'').replace(' ','')[1:-1]
    if i < spamPerc :
        trainList.append(str1.split(','))
    else:
        testList.append(str1.split(','))


testbaged = BagOfWords(testList)
trainbaged = BagOfWords(trainList)







NaiveBayes(trainbaged,testbaged)

