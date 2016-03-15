"""
Author:   Kevin Murphy
Date:     2/11/2016

This program will scrape data off http://tourneymachine.com
relating to tournaments and their teams.  It will then organize
and output that data into ?csv? files."""

import requests as rq
import datetime as dt
#import cPickle as cp
import csv
import argparse
import gc

arg = argparse.ArgumentParser(description='')

arg.add_argument('--min', default='17100')
arg.add_argument('--max', default='17160')
arg.add_argument('--d', action='store_true', default=False)
arg.add_argument('--sv', action='store_true', default=False)
arg.add_argument('--l', action='store_true', default=False)
arg.add_argument('--f', action='store_true', default=False)
arg.add_argument('--ff',action='store_true', default=False)

args = arg.parse_args()

GLOBAL_MIN = '00001' # Web scraper will start with this id
GLOBAL_MAX = '17965' # Web scraper will end with this id
MIN = args.min       # Custom start-value
MAX = args.max       # Custom end-value
if MIN < GLOBAL_MIN: MIN = GLOBAL_MIN
if MAX > GLOBAL_MAX: MAX = GLOBAL_MAX
DEBUG = args.d       # Show details
SAVE = args.sv       # Save complexes to an independent file.
LIST = args.l        # Save each complex to a list.  Note: this will
                     # significantly slow down the program.
FTEAMS = args.f      # Program will attempt to find websites for each team.
FTOURNS = args.ff    # Program will attempt to find websites for each tourn.

if SAVE: LIST = True

T_LIST = []
T_URLS = []
CONTACTS = []

class Tourn():    
    def __init__(self, u):
        self.complexes = []
        self.divs = []
        self.long_url = ''
        self.url = ''
        self.name = ''
        self.sport = ''
        self.date_created = ''
        self.play_date = ''
        self.dates = ''
        self.location = ''
        self.note = ''
        self.gps = []
        
    def addComp(self, c):
        if (c.lat, c.lon) != ('0.0', '0.0'):
            self.gps.append((c.lat, c.lon))
        if self.checkCompHandled(c):
            return
        else:
            self.complexes.append(c)

    def checkCompHandled(self, c):
        compNames = [c.ID for c in self.complexes]
        return compNames.count(c.ID)

    def addDiv(self, d):
        d.name = d.name.replace('Division: ','')
        d.name = d.name.replace('&amp;','&')
        self.divs.append(d)
        self.divs = list(set(self.divs))

    def findDivID(self, name):
        divNames = [str(d.name) for d in self.divs]
        try:
            i = divNames.index(str(name))
            return i
        except ValueError:
            return
            
    def addTeam(self, t, d):
        div_id = self.findDivID(d.name)

        if type(div_id) == int:
            self.divs[div_id].teams.append(t)
        else:
            self.addDiv(d)
            div_id = self.findDivID(d.name)
            self.divs[div_id].teams.append(t)

    def longUrl(self, u):
        self.long_url = u
        self.ID = self.long_url[74:]
        self.date_created = self.ID[1:9]
        
    def show(self):
        print(self.name)
        print(self.ID)
        print('')
        print(self.sport)
        print('Date created: ' + self.date_created)
        print('Date games:   ' + self.dates)
        print(self.location)
        print(self.gps)
        print(self.note)
        print('url: ' + self.url)
        print('url: ' + self.long_url)
        print('#ds: ' + str(len(self.divs)))
        print('#cs: ' + str(len(self.complexes)))
        print('')

    def showClean(self):
        print(self.name)
        print(self.dates)
        print(self.sport)
        print(self.location)
        
class Complex():
    def __init__(self, i='', n='', la='', lo=''):
        self.ID = i
        self.name = n
        self.lat = la
        self.lon = lo

    def show(self):
        print(self.ID)
        print(self.name)
        print(self.lat)
        print(self.lon)
        print('')

class Div():
    def __init__(self, n=''):
        self.name = n
        self.teams = []

    def show(self):
        print('%s (%d teams)' % (self.name, len(self.teams)))

class Team():
    def __init__(self):
        self.ID = ''
        self.name = ''

    def show(self):
        print('\t%s\t%s' % (self.ID, self.name))

def writeToFile(obj):
    with open('output2.txt', 'a') as f:
        cp.dump(obj, f)

def readFromFile():
    with open('output2.txt', 'r') as f:
        cp.load(f)

    for o in gc.get_objects():
        if isinstance(o, Tourn):
            print(o.name)
            
def grabData(t):
    i = t.index('<a id="tournamentHeader1_ui_Tournament_HyperLink') + 119
    j = t[i:].index('</a') + i
    T.name = t[i:j]

    i = t.index('tournamentDates') + 35
    j = t[i:].index('  ') + i - 1
    T.dates = t[i:j]

    i = t.index('tournamentLocation') + 38
    j = t[i:].index('  ') + i - 1
    T.location = t[i:j]

    try:
        i = t.index('tournamentNoteClose') + 133
        j = t[i:].index('</p') + i - 21
        T.note = t[i:j]
    except ValueError: pass
    
    i = t.index('tournamentUrl') + 22
    j = t[i:].index('"') + i
    T.url = t[i:j]

    i = t.index('tournamentSport') + 131
    j = t[i:].index('<') + i - 9
    T.sport = str(t[i:j].strip(';p').strip())
    if T.sport == 'ccer': T.sport = 'Soccer'
    
    for c in range(t.count('var complex')): # Grab all of the complexes
        com = Complex()

        i = t.index('complex' + str(c) + '.ID') + 15
        j = t[i:].index("';") + i
        com.ID = t[i:j]

        i = t.index('complex' + str(c) + '.name') + 17
        j = t[i:].index("';") + i
        com.name = t[i:j]

        i = t.index('complex' + str(c) + '.lat') + 16
        j = t[i:].index("';") + i
        com.lat = t[i:j]

        i = t.index('complex' + str(c) + '.long') + 17
        j = t[i:].index("';") + i
        com.lon = t[i:j]
        
        T.addComp(com)

    i = t.index('tournamentHeader1$ui_TextTeam_DropDownList')
    j = t[i:].index('</select') + i
    block = t[i:j]

    for tm in range(block.count('<option value="')): # Grab all teams/divs
        div = Div()
        team = Team()

        i = block.index('<option value="') + 15
        j = block[i:].index('</option') + i
        line = block[i:j]
        block = block[j:]

        if line == '">': continue

        team.ID = line[:32]
        team.name = line[34:line.index(' (Division')]
        div.name = line[line.index(' (Division') + 2:-1]

        T.addTeam(team, div)
        
def tryURL(url):
    r = rq.get(url)
    T.longUrl(rq.head(url, allow_redirects=True).url)
    
    print('%s %d' % (url, len(r.text)))
    no_404 = len(r.text) > 40000
    
    return no_404
    
def printData():
    for t in T_LIST:
        print('-' * 100)
        t.show()
        for c in t.complexes:
            c.show()
        for d in t.divs:
            d.show()
            for tm in d.teams:
               tm.show()
        print('-' * 100)
        print(' * ' * 33)

def makeURL(r):
    global T

    base_url = 'http://www.tourneymachine.com/R'
    url = base_url + r

    T = Tourn(url)

    if tryURL(url):
        grabData(rq.get(url).text)
        if T.sport != 'Lacrosse':
            print T.sport
            return
        if LIST: T_LIST.append(T)
        if SAVE: writeToFile(T)
        if FTEAMS: findTeamsUrl()

def stitchUrl(full, ext):
    try:
        while ext[0] == '.' or ext[0] == '/':
            ext = ext[1:]
        pieces = full.split('/')
        url = 'http://' + pieces[2] + '/' +  ext
        return url
    except IndexError:
        return full
    
def findTeamsUrl():
    for d in T.divs:
        for t in d.teams:
            findTeamUrl(d,t)

def un_http(s):
    s = s.replace('%3F','?')
    s = s.replace('%3D', '=')
    s = s.replace('&amp;', '&')
    s = s.replace('%23', '#')
    s = s.replace('"','')
    s = s.replace("'",'')
    if '>' in s: s = s[:s.index('>')]

    return s

def fixName(n, e):
    n = un_http(n)
    if len(n.split(' ')) > 3 or n == 'Email' or '<' in n or e in n:
        n = ''
        
    return n
    
def fixEmail(e):
    e = un_http(e)
    e = e.split(' ')[0]
    e.replace('"', '')
    if '@' not in e or '.' not in e or 'tourneymachine.com' in e:
        e = ''
    if '?' in e:
        e = e[:e.index('?')]

    return e
    
def getEmail(html, team, sport, k=0):
    for a in range(html.text.count('mailto:')):
        i = html.text[k+1:].index('mailto:') + 1
        block = html.text[i+k-60:i+k+100]
        k += i
        #print '>>>', block
        try:
            i = block.index('mailto:') + 7
            j = block[i:].index('">') + i
            email = block[i:j]
        except ValueError: email = ''

        try:
            i = block.index('">') + 2
            j = block[i:].index('</a') + i
            name = block[i:j]
        except ValueError: name = ''

        email = fixEmail(email)
        name = fixName(name, email)
        #print 'took: %s, %s' % (email, name)

        if len(email):
            row = [team.encode('utf-8'), email.encode('utf-8'),
                   name.encode('utf-8'), sport.encode('utf-8'),
                   str(dt.date.today())]
            saveContactInfo(row)

def saveContactInfo(r):
    print(r)
    try:
        with open('contacts.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(r)
    except UnicodeEncodeError:
        print 'Error encoding unicode for ' + r
    
def findTeamUrl(div, tm):
    #print('%s, %s, %s' % (div.name, tm.name, T.sport))
    query = tm.name + ' ' + T.sport
    r = rq.get('http://google.com/search', params={'q' : query})
    i = r.text.index('"topstuff"')
    i = r.text[i:].index('url?q') + i + 6
    j = r.text[i:].index('&amp;sa=') + i

    url = r.text[i:j]
    url = un_http(url)

    contactUrls = [url]

    #print url
    for keyword in ['Contact', 'Staff', 'About', 'Team']:
        try:
            r = rq.get(url)
            k = 0
            for f in range(r.text.count(keyword)):
                i = r.text[k+1:].index(keyword) + 1
                block = r.text[i+k-100:i+k+100]
                k += i
                
                try:
                    i = block.index('href') + 6
                    j = block[i:].index(" ") + i
                    contactUrl = block[i:j]
                    contactUrl = un_http(contactUrl)
                    if contactUrl[0:4] != 'http':
                        contactUrl = stitchUrl(url, contactUrl)
                    contactUrls.append(contactUrl)
                except ValueError: pass
        except rq.exceptions.ConnectionError: pass
        except rq.exceptions.TooManyRedirects: pass

    for u in contactUrls:
        try:
            r = rq.get(u)
            getEmail(r, tm.name, T.sport)
        except rq.exceptions.InvalidURL:
            print 'Invalid url: %s' % u
        except rq.exceptions.SSLError:
            print 'Untrusted certificate for url: %s' % u
        except rq.exceptions.MissingSchema:
            print 'Missing schema: %s' % u
        except rq.exceptions.ConnectionError:
            print 'Unable to connect to: %s' % u
        except rq.exceptions.TooManyRedirects:
            print 'Too many redirects at: %s' % u
        
    #print('\n\n\n\n')
    return True
        
def main():
    for u in range(int(MIN), int(MAX)):
        makeURL(str(u))
    if SAVE: readFromFile()
    printData()
    
main()
