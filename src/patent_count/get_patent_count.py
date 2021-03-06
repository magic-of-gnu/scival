import urllib.parse as urlp
import os
import numpy as np
import pandas as pd
from pprint import pprint as pp
import logging

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time
from numpy.random import uniform as runi

from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


BASE_DIR = os.path.abspath(os.path.realpath(__file__))
BASE_DIR = os.path.join(os.path.dirname(BASE_DIR), '..', '..')
os.chdir(BASE_DIR)

FOLNAME_AFF_SEARCH = os.path.join(BASE_DIR, 'data', 'aff_search')
FOLNAME_METRIC_RESPONSE = os.path.join(BASE_DIR, 'data', 'metric_response')

key_aff = 'Institution'
key_acc = 'id_downloaded'
key_id  = 'id'
key_met = 'metrics'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create file handler which logs info messages
fh = logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'logs.txt'), 'w', 'utf-8')
fh.setLevel(logging.DEBUG)

# create console handler with a debug log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# creating a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-8s: %(message)s')

# setting handler format
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


def extract_integer_(patent_value):

    a = 0

    try:
        logger.debug('extracting integer from patent_value')
        a  = extract_integer(patent_value)
    except:
        logger.debug('error during integer extraction')
        a = 0

    return a


def driver_has_element_by_xpath(driver, xpath):

    try:
        driver.find_element_by_xpath(xpath)
        return True
    except:
        return False


def close_pop_up_window(driver):

    try:
        # driver.find_element_by_xpath("//button/[@id='_pendo-close-guide_']").click()
        driver.find_element_by_xpath("//button[@id='_pendo-close-guide_']").click()
        logger.debug('extra pop_up_window was close')
    except:
        pass


def get_valid_ids(df, key, n, valid_values=None, bad_values=None):
    '''this function gets the valid indices'''

    valid_values = [np.nan] or valid_values
    bad_values = [-1] or bad_values

    # a = df.loc[:, key]

    valid_inds = []

    inds = df.index.tolist()

    i = 0
    j = 0

    while(True):

        if j > df.shape[0]:
            break

        if i == n:
            break

        # coutns only nans
        if np.isnan(df.loc[inds[j], key]):
            valid_inds.append(inds[j])
            i = i+1

        if i % 10 == 0 and i != 0:
            logger.debug('getting valid inds, i is {}'.format(i))

        j = j + 1

    print('valid inds are ')
    print(valid_inds)

    return valid_inds




class my_df(pd.DataFrame):

    def __init__(self):

        super().__init__(self)
        self.i = 0

    def my_iterrows(self):
        a = self.iterrows()
        self.i = self.i + 1
        return a

    def get_valid_id(self, key=None):

        q = 0

        while(True):
            
            a = next(self.iterrows())

            print(a)
            q = q + 1

            if q % 5 == 0:
                break
            

def open_scopus_link(driver):
    '''
    open the advanced search of scopus
    '''
    # binary = FirefoxBinary('/usr/lib/firefox/firefox')
    # driver = webdriver.Firefox(firefox_binary=binary)
    driver.implicitly_wait(2) # seconds

    # l = 'https://www.nobelprize.org/nobel_prizes/physics/laureates/index.html'
    main_scopus2 = 'https://www.scopus.com/sources?zone=&origin=NO%20ORIGIN%20DEFINED'
    main_search = 'https://www.scopus.com/search/form.uri?zone=TopNavBar&origin=sbrowse&display=basic'
    adv_search = 'https://www.scopus.com/search/form.uri?display=advanced&clear=t&origin=searchbasic&txGid=fc476bc6f6c3a112a577edd9f6f26e14'

    # to get to advanced search, we need to go through several links
    driver.get(main_scopus2)
    t = runi(10 + runi(-3, 1))
    logger.debug('opened main link, waiting for {} s'.format(t))
    time.sleep(t)
    # driver.implicitly_wait(10) # seconds

    close_pop_up_window(driver)

    driver.get(main_search)
    t = runi(10 + runi(-3, 1))
    logger.debug('opened search link, waiting for {} s'.format(t))
    time.sleep(t)
    # driver.implicitly_wait(10) # seconds


    close_pop_up_window(driver)

    driver.get(adv_search)
    t = runi(10 + runi(-3, 1))
    logger.debug('opened advanced search link, waiting for {} s'.format(t))
    time.sleep(t)
    # driver.implicitly_wait(10) # seconds

    close_pop_up_window(driver)

    return driver


def extract_integer(a):
    n = [np.int(x) for x in a.split() if x.isdigit()] or [0]
    return n[0]


def unparse(l):
    main_link, query = l.split('?')

    a = query.split('&')

    b = [x.split('=') for x in a]
    params = dict(zip([x[0] for x in b], [x[1] for x in b]))

    q = params['s'].split('AND')
    qparams = [urlp.unquote_plus(x).strip() for x in q]

    params['q'] = qparams
    params['main_link'] = main_link

    return params


def get_patent_count(driver, query):

    # click to activate the textField
    # sometimes we need to click 'contentEditLabel', sometimes 'searchfield'
    logger.debug('clicking on search input field')
    try:
        logger.debug('clicking on contentEditLabel')
        driver.find_element_by_id('contentEditLabel').click()
    except Exception as e:
        logger.debug('clicking on searchfield')
        driver.find_element_by_id('searchfield').click()

    # fill the textfield and send the request
    element = driver.find_element_by_id('searchfield')

    logger.debug('clearing search field')
    element.clear()
    # time.wait(runi(0, 0.2))
    logger.debug('entering query into search field')
    element.send_keys(query, Keys.RETURN)

    t = 4 + runi(0, 1)
    time.sleep(t)


    logger.debug('waiting for page to be downloaded')
    # get amount of patents
    el = wait(driver, 5).until(EC.presence_of_element_located((By.ID, "searchResFormId")))

    current_url = driver.current_url
    driver.get(current_url)

    t = 4 + runi(0, 1)
    time.sleep(t)

    if driver_has_element_by_xpath(driver, '//div[@class="alert alert-danger"]/a[@class="close"]'):
        logger.debug('no document found for here')
        a = 0
        return a
    else:

        a = 0

        try:
            logger.debug('retrieving patent_count')
            patent_hidden_element = driver.find_element_by_id('hubLinksContainer')
            if patent_hidden_element.get_attribute('class') == 'hidden':
                logger.debug('no patent elements were found')
                patent_value = 0
            else:
                patent_element = driver.find_element_by_id('patentLink')
                patent_value = patent_element.text

        except:
            driver.find_element_by_xpath("//button[@title='Edit search query']").click()
            assert 'something happened'

        else:

            logger.debug('patent_value is {}'.format(patent_value))

            a = extract_integer_(patent_value)

            logger.debug('extracted integer is {}'.format(a))

            t = 2 + runi(0, 1)
            time.sleep(t)

            try:
                logger.debug('clicking on editAuthSearch')
                driver.find_element_by_id('editAuthSearch').click()
            except:
                logger.debug('error during clicking on editAuthSearch')
                logger.debug('instead find "Edit search query" field by force')
                driver.find_element_by_xpath("//button[@title='Edit search query']").click()

            t = 2 + runi(0, 1)
            time.sleep(t)

            return a

def main(n, year, fname_df, fname_res):

    slink = 'https://www.scopus.com/results/results.uri?sort=plf-f&src=s&sid=9cf773e35f9165af3488aaee575fd58a&sot=a&sdt=a&sl=49&s=affil%28%22University+of+Toronto%22%29+AND+pubyear+%3d+2016&origin=searchadvanced&editSaveSearch=&txGid=7bfd7d6ce111fb51284b6d3d7d6149ee'

    plink = 'https://www.scopus.com/results/results.uri?src=p&sort=plf-f&sid=9cf773e35f9165af3488aaee575fd58a&sot=a&sdt=a&sl=49&s=affil%28%22University+of+Toronto%22%29+AND+pubyear+%3d+2016&cl=t&offset=1&ss=plf-f&ws=r-f&ps=r-f&cs=r-f&origin=resultslist&zone=queryBar'

    # n = 15
    # year = 2015

    logger.debug('downloaded results table')


    # fname_df = os.path.join('data', 'universities_table.csv')
    # fname_res = os.path.join('data', 'patent_count.csv')
    logger.debug('loading df with acknowledgements')
    df = pd.read_csv(fname_df).set_index('Institution').sort_values(by=['order'])
    # df = pd.read_excel(fname_df).set_index('Institution').sort_values(by=['order'])


    key = 'patent_downloaded_{}'.format(year)
    logger.debug('loading affiliations that needs to be processed, key is {}, n is {}'.format(key, n))
    valid_aff_names = get_valid_ids(df, key, n)
    # valid_aff_names = get_valid_ids(df.set_index('Institution'), key, n)

    logger.debug('opening browser with scopus advanced search link')

    timeout = 30

    binary = FirefoxBinary('/usr/lib/firefox/firefox')
    driver = webdriver.Firefox(firefox_binary=binary)
    driver.set_page_load_timeout(timeout) # error if timeout has passed


    try:
        driver = open_scopus_link(driver)
        cur_res = []


        logger.debug('doing search')
    except:
        logger.warning('error has occured during opening browser')

    else:


        for x in valid_aff_names:
            aff_name = x
            # aff_name = valid_aff_names[i]
            patent_count = 0

            logger.debug('creating query for search')
            query = 'affil("{}") AND pubyear = {}'.format(aff_name, year)
            logger.debug('query is {}'.format(query))

            try:
                logger.debug('getting patent_count for {}'.format(aff_name))
                patent_count = get_patent_count(driver, query)

            except TimeoutException as e:
                logger.warning('timeout error')
                break

            except Exception as e:
                logger.warning('error has occured')

                df.at[aff_name, key] = -1
                break

            else:

                logger.debug('number of patents has been retrieved succesfully')
                logger.debug('number of patents for {} is {}'.format(aff_name, patent_count))
                logger.debug('updating acknowledgment df at [{}, {}]'.format(aff_name, key))
                df.at[aff_name, key] = 1

                logger.debug('storing results')
                cur_res.append({'name': aff_name,
                                'year': year,
                                'metricType': 'patentCount',
                                'valueByYear': patent_count})


        logger.debug('creating the resultant DataFrame')
        res = pd.concat([pd.DataFrame(cur_res), pd.read_excel(fname_res)])

        logger.debug('saving the results')
        res.to_excel(fname_res, index=False)
        df.to_csv(fname_df)


    finally:
        driver.quit()
        pass

    return driver



if __name__ == "__main__":

    # n = 15
    # year = 2015
    # fname_df = 
    # fname_res = 

    n = 15

    year = 2012
    years = [2012, 2013, 2014, 2015, 2016]
    # years = [2012]

    fname_df = os.path.join('data', 'universities_table.csv')
    fname_res = os.path.join('data', 'patent_count.xlsx')

    for i in range(5):
        for year in years:

            driver = main(n=n, year=year, fname_df=fname_df, fname_res=fname_res)
            time.sleep(5)
