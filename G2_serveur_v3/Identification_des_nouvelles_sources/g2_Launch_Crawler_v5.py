# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 11:39:57 2021

@author: degau
"""


########## Module import ##########

# Files
import json
import pandas as pd

# Maths
import random

# Extraction
import re

# Scraping
import scrapy
from requests import get

# Parsing
from urllib.parse import urlencode

# Format
from datetime import datetime
from datetime import timedelta
import time


########## Functions ##########

def create_google_url(query, nb_results):
    """
    Allows you to create a Google URL from a keyword

    Parameter :
        query : keyword to enter in the search bar

    Out :
        google_url : google URL created from the keyword
    """
    # num = number of results to be scraped
    google_dict = {'q': query, 'num': nb_results, }
    google_url = 'http://www.google.com/search?' + urlencode(google_dict)
    return google_url


def combAND(couple):
    """Documentation
    Parameters:
        couple: a list of 2 Strings
    Out :
        list : a combination of the 2 members of a couple with AND between them
    """

    return str(couple[0])+' '+'AND'+' '+str(couple[1])


def listToAND(listCouple):
    """Documentation
    Parameters:
        listCouple: a list of couple

    Out :
        list : a list of the combination of the couple of listCouple
    """

    # We use combAND
    return [combAND(i) for i in listCouple]


def combOR(tuple):
    """Documentation

    Parameters:
        tuple: a list of String

    Out :
        final : a combination of the members of the tuple with OR between them
                and framed with ()
    """

    # First step : initialisation of final
    final = '('+str(tuple[0])+')'
    # Second step : adding the rest of the tuple
    for i in range(1, len(tuple)):
        final = final+'|'+'('+tuple[i]+')'
    return final


# Applying the previous function to a list of tuple
def listToOR(listTuple):
    """Documentation
    Parameters:
        listTuple: a list of tuples

    Out :
        list : a list of the combination of the tuple of listTuple
    """

    # We use combOR
    return [combOR(i) for i in listTuple]


# Making a list of random tuples
# We have to limit the number of request, by default 1000, and we make couples
def listComb(listAND, numbT=2, iteration=int(1000)):
    """Documentation

    Parameters:
        listAND: a list Strings with AND
        numbT : the length of the tuple we want to create
        iteration : the maximum number of combination we want to create

    Out :
        finalList : a list of the combination of the tuple of listTuple
    """

    finalList = []
    i = 0
    # Step 1 : we loop until we have enough tuples or the list is empty
    while ((len(listAND) >= numbT) and (i < iteration)):
        i += 1
        # Step 2 : at each loop, we take some random elements of listAND and
        # create a tuple with them
        listRand = random.sample(listAND, numbT)
        # Step 3 : we remove the elements from listAND
        for j in listRand:
            listAND.remove(j)
        # Step 4 :we add the tuple we created to our finalList
        finalList.append(listRand)
    return finalList


def link_filter_date(link, date_filter):
    """Documentation
    Function that allows to add a "limit date" parameter in the link

    Parameters:
        link : URL to which the date filter should be added
        date_limit : Limit date

    Out :
        link_new : URL with a date filter
    """

    date_limit = datetime.strptime(date_filter, '%Y-%m-%d')
    # Crawling 1 day before last crawling date
    days_to_substract = timedelta(days=1)
    
    # Limit date
    date_limit = date_limit - days_to_substract
    jour = str(date_limit.day)
    mois = str(date_limit.month)
    annee = str(date_limit.year)

    link_new = link+"&source=lnt&tbs=cdr%3A1%2Ccd_min%3A"+mois+"%2F"+jour+"%2F"+annee+"%2Ccd_max%3A&tbm="
    return link_new


def get_url(url, date_filter, API_KEY):
    """
    Creation of the URL that will allow the legal scraping of Google results
    (use of the API key). This URL is equivalent to a Google search.

    Parameter :
        url : google URL created from the keyword

    Out :
        proxy_url : URLs built using the API
    """

    payload = {'api_key': API_KEY,
               'url': url,
               'autoparse': 'true',
               'country_code': 'fr',
               # Depersonalisation of results
               'pws': 0}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    date_url = link_filter_date(proxy_url, date_filter)
    return date_url


class GoogleSpider(scrapy.Spider):
    """
    This class lists functions for scraping Google results from a list of keywords
    """

    # GoogleSpider class name
    name = 'google'
    # Name of the site to be scraped
    allowed_domains = ['www.google.com']
    # Settings
    custom_settings = {
                        # Criticality level at which the log is displayed
                        'LOG_LEVEL': 'INFO',
                        # Maximum number of simultaneous requests
                        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
                        # 'CONCURRENT_REQUESTS': 2,
                        # 'CONCURRENT_ITEMS': 200,
                        # Maximum number of retries to be made if the query fails
                        'RETRY_TIMES': 0}

    def start_requests(self, listCouple, API_KEY, length, requestNumber, date_filter, nb_results):
        # Initialisation of DataFrame
        df = pd.DataFrame(columns=['URL', 'Query'])
        # Format changeover
        lWork = listToAND(listCouple)
        # Selection of queries
        lWork = listComb(lWork, numbT=length, iteration=requestNumber)
        # We change the format of Keywords
        lWork = listToOR(lWork)

        lURL = []
        # We loop the keywords to generate the queries
        print(lWork)
        for query in lWork:
            url = create_google_url(query, nb_results)
            lURL.append(str(scrapy.Request(get_url(url, date_filter, API_KEY),
                                           meta={'pos': 0}))[5:-1])
        # Column generation
        df['Query'] = lWork
        df['URL'] = lURL

        yield df


########## Launch crawling ##########

def Launch_Crawler(p_listCouple,
                   API_KEY,
                   p_date,
                   p_length,
                   p_requestNumber,
                   p_nb_results,
                   path_general,
                   path_links_crawler,
                   path_backup,
                   path_files):
    
    
    ########## Start building URLs ##########
    
    df_result = list(GoogleSpider().start_requests(p_listCouple,
                                                   API_KEY,
                                                   p_length,
                                                   p_requestNumber,
                                                   p_date,
                                                   p_nb_results))[0]
    
    
    ########## Crawling of Google results ##########
    
    # Crawling start time
    print("Crawling start time : "+datetime.now().strftime("%H:%M:%S"))
    
    list_source = []
    i = 0
    
    for index, row in df_result.iterrows():
        link = row['URL']
        query = row['Query']
        # 1 minute break to avoid API overloading
        time.sleep(60)
        # URL scraping
        response = get(link)
    
        # Test if the request was successful
        if response.status_code == 200:
            # Addition of the scraped google results and the corresponding query
            list_source.append([response.text, query])
    
            i += 1
            # Saving the results every 20 queries
            if (i % 20 == 0):
                with open(path_backup+'etape'+str(i)+'.json', 'w') as jsonfile:
                    json.dump(list_source, jsonfile)


    # Crawling end time
    print("Crawling end time : "+datetime.now().strftime("%H:%M:%S"))
    date_crawling = datetime.now().strftime("%Y-%m-%d")


    # Storing the crawling date
    with open(path_files+'date_last_crawling.txt', 'w') as file:
        file.write(date_crawling)
    
    
    ########## Processing of results ##########
    
    links = []
    title = []
    query = []
    resume = []
    position = []
    
    # Pattern for extracting URLs
    pattern = re.compile("\"position\"[^}]+")
    pattern_link = re.compile("\"link\"[^,]+")
    pattern_title = re.compile("\"title\"[^,]+")
    pattern_resume = re.compile("\"snippet\"[^,]+")
    pattern_pos = re.compile("\"position\"[^,]+")

    df_sources = pd.DataFrame(columns=['URL','Query','Title','Snippet','Rank'])
    
    for source in list_source:

        # Finding patterns in the scraped results
        clean = pattern.findall(str(source[0]))
        # Sorting the results
        clean_order = dict.fromkeys(clean)
        my_links = list(dict.fromkeys([x for x in clean_order]))
        
        # Extraction of URLs, titles, snippets and positions
        for i in my_links:
            link = pattern_link.findall(i)
            titre = pattern_title.findall(i)
            snippet = pattern_resume.findall(i)
            pos = pattern_pos.findall(i) 
            try :
                url = link[0][8:-1]
                # Check that the URL is a result (different from Google)
                if "https://www.google" not in url:
                    links.append(url)
                    title.append(titre[0][9:-1])
                    query.append(source[1])
                    resume.append(snippet[0][11:])
                    position.append(int(pos[0][11:]))
            except :
                a=1
        
   
    df_sources['URL'] = links
    df_sources['Query'] = query
    df_sources['Title'] = title
    df_sources['Snippet'] = resume
    df_sources['Rank'] = position 
        

    # Storing the data in JSON format
    df_sources.to_json(path_links_crawler+'liens_crawler.json', orient='index')
        
    
    return df_sources
    


    
    

    
    
    
    