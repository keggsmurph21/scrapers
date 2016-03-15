"""
Author:   Kevin Murphy
Date:     3/14/2016
"""

import requests as rq
import datetime as dt
import webbrowser as wb
import csv
import argparse

def buildRankingsUrl(level, gender, age, region, state, page=1):
    r = rq.get('http://home.gotsoccer.com/rankings/results.aspx',
               params={'Level' : level, 'Gender' : gender, 'Age' : age,
                       'Region' : region, 'State' : state, 'Page' : page})
    return r

def getDataFromRankings(r):
    teams = r.text.split('TeamTierBox')[1:]
    for t in teams:
        i = t.index('teamid=') + 7
        j = i + 6
        teamid = t[i:j]

        i = t.index('LinesTableLink') + 19
        j = t[i:].index('</b') + i
        teamname = t[i:j]

        i = t.index('#CD5C5C') + 12
        j = i + 2
        teamstate = t[i:j]

        r = rq.get('http://home.gotsoccer.com/rankings/team.aspx',
               params={'teamid' : teamid})

        getDataFromTeamGS(r)
        
def getDataFromTeamGS(r):
    try:
        i = r.text.index('<a id="ctl00_MainContent_ClubWebsite"') + 61
        j = r.text[i:].index(' ') + i - 1
        url = r.text[i:j]
        print url
        r = rq.get(url)
        getDataFromTeam(r)
        
    except ValueError:
        print r.url
    except rq.exceptions:
        print r.url

def un_http(s):
    s = s.replace('%3F', '?')
    s = s.replace('%3D', '=')
    s = s.replace('&amp', '&')
    s = s.replace('%23', '#')
    s = s.replace('"', '')
    s = s.replace("'", '')
    if '>' in s: s = s[:s.index('>')]

    return s

def stitchUrl(full, ext):
    try:
        while ext[0] == '.' or ext[0] == '/':
            ext = ext[1:]
        pieces = full.split('/')
        url = 'http://' + pieces[2] + '/' + ext
        return url
    except IndexError:
        return full
    
def getDataFromTeam(r):
    contactUrls = [r.url]
    
    for keyword in ['Contact', 'Staff', 'About', 'TEAMS']:
        try:
            k = 0
            for f in range(r.text.count(keyword)):
                i = r.text[k+1:].index(keyword) + 1
                block = r.text[i+k-100:i+k+100]
                k += i

                try:
                    i = block.index('href') + 6
                    j = block[i:].index(' ') + i
                    contactUrl = block[i:j]
                    contactUrl = un_http(contactUrl)
                    if contactUrl[0:4] != 'http':
                        contactUrl = stitchUrl(r.url, contactUrl)
                    contactUrls.append(contactUrl)
                except ValueError:
                    pass
        except rq.exceptions.ConnectionError: pass

    print contactUrls
    for u in contactUrls:
        try:
            r = rq.get(u)
            getEmail(r)
        except rq.exceptions:
            print 'Requests has returned an exception for %s' % u

def fixEmail(e):
    e = un_http(e)
    e = e.replace('Email: ','')
    e = e.split(' ')[0]
    e = e.replace('"', '')
    e = e.replace('%20', '')
    if '@' not in e or '.' not in e:
        e = ''
    if '?' in e:
        e = e[:e.index('?')]

    return e

def getEmail(r, k=0):
    for e in range(r.text.count('mailto:')):
        i = r.text[k+1:].index('mailto:') + 1
        block = r.text[i+k-60:i+k+100]
        k += i

        try:
            i = block.index('mailto:') + 7
            j = block[i:].index('">') + i
            email = block[i:j]
        except ValueError: email = ''

        email = fixEmail(email)

        if len(email):
            row = [email.encode('utf-8')]

            print row

    for domain in ['@gmail.com', '@yahoo.com', '@hotmail.com', '@verizon.net']:
        k = 0
        splitByTeam = r.text.encode('utf-8').split(domain)[:-1]
        for t in splitByTeam:
            try:
                block = t[-30:]
                email = block[block.index('>')+1:] + domain
                email = fixEmail(email)
            except ValueError: email = ''
        
            if len(email):
                row = [email.encode('utf-8')]
                
                print row


def main():
    for page in range(187):
        r = buildRankingsUrl('National', 'Boys', '11', '', '', page)
        getDataFromRankings(r)
    
main()
