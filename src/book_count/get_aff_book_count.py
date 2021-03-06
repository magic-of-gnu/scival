# from scopus import ScopusSearch
import os
import pandas as pd
import numpy as np
import logging
from urllib import parse, request
import urllib.error
import json
from pprint import pprint as pp


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
fh = logging.FileHandler(os.path.join(BASE_DIR, 'logs.txt'), 'w', 'utf-8')
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


class my_scopus_search():

    def __init__(self, query=None, apiKey=None, httpAccept=None, logger=None):

        httpAccept = httpAccept or "application/json"
        apiKey = apiKey or "7f59af901d2d86f78a1fd60c1bf9426a"

        if query is None:
            raise("query is not given, please, give it")

        self.query = query
        self.httpAccept = httpAccept
        self.apiKey = apiKey
        self.logger = logger or logging.getLogger(__name__)
        self.response = None
        self.jres = None

        self.logger.debug("my_scopus_search class was initialized")
        self.__url = "https://api.elsevier.com/content/search/scopus"
        self.http_error = None


    def encode(self):
        """encode query"""

        self.parsed_url = self.__url + "?query=" + parse.quote_plus(self.query, safe='()')
        self.parsed_url = "&".join([self.parsed_url, "apiKey={}".format(self.apiKey), "httpAccept={}".format(parse.quote(self.httpAccept, safe=""))])

        self.logger.debug("encoding query to {}".format(self.parsed_url))
        return self


    def send_request(self):
        """send request"""

        response = None

        try:
            self.logger.debug("sending the request")
            response = request.urlopen(self.parsed_url)

            self.logger.debug("request retrieved sucessully")
        except urllib.error.HTTPError as e:

            self.http_error = e.code

            if e.code == 404:
                self.logger.warning("NOT FOUND")
                self.logger.warning("error is {}".format(e))
            elif e.code == 400:
                self.logger.warning("invalid request, try again")
                self.logger.warning("error is {}".format(e))
            elif e.code == 401:
                self.logger.warning("cannot be authentified due to missing/invalid credentials")
                self.logger.warning("error is {}".format(e))
            elif e.code == 429:
                self.logger.warning("quota exceeded")
                self.logger.warning("error is {}".format(e))
            else:
                self.logger.warning("unkown error")
                self.logger.warning("error code is {}".format(e))

        except Exception as e:

            response = None
            self.logger.warning("request retrieved with error, the error code is ", e)

        self.response = response
        return self


    def read_json(self):

        if self.response is not None:
            output = json.loads(self.response.read())
            self.jres = output


    def get_search_object(self):

        self.logger.debug('start encoding')
        self.encode()
        self.logger.debug('encoding finished')

        self.send_request()
        self.read_json()

        return self.jres



class my_df():

    def __init__(self, df, logger=None):

        self.logger = logger or logging.getLogger(__name__)
        self.df = df.copy()
        self.i = 0
        self.n_rows = df.shape[0]
        self.inds = df.index.tolist()

        self.logger.debug("class was initialized")


    def next_row(self):

        if self.i < self.n_rows:

            row = self.df.loc[self.inds[self.i], :]
            self.i = self.i + 1
            return row

        else:
            self.logger.warn("reached the end of the file")
            raise("the end of df reached")


    def next_aff(self, col_name):

        isfree = 0

        while isfree == 0:
            row = self.next_row()

            if np.isnan(row[col_name]):
                isfree = 1

        return row.name


class scopus_query:

    """in this class I define those keys I need to use to extract number of books for each university
    this means that this class is applicable only in certain cases

    for more instructions, please, read this:
    https://dev.elsevier.com/tips/ScopusSearchTips.htm

    """

    def __init__(self, year=None, affil=None, doctype=None):

        self.q = dict()
        self.query = None   # a final string the query
        self.set_values(year=year, affil=affil, doctype=doctype)


    def set_values(self, year=None, affil=None, doctype=None):

        if year is None:
            year = 2012

        if affil is None:
            affil = 'Harvard University'

        if doctype is None:
            doctype = "bk"

        self.affil = affil
        self.doctype = doctype
        self.year = year
        self.q = dict()
        self.query = None

        return self


    def encode(self):
        self.q['affil']   = 'affilorg("{}")'.format(self.affil)
        self.q['doctype'] = "doctype({})".format(self.doctype)
        self.q['year']    = "pubyear = {}".format(self.year)

        return self


    def set_query(self):

        self.query = " AND ".join([self.q[key] for key in self.q.keys()])
        self.query.encode()

        return self

    def get_query(self):
        return self.query



if __name__ == "__main__":


    aff_fname = "universities_table.csv"
    fname_aff_book_count = os.path.join(BASE_DIR, "data", aff_fname)

    df_af = pd.read_csv(fname_aff_book_count).set_index("Institution")

    df_aff = my_df(df_af, logger=logger)

    MY_API_KEY = "e53785aedfc1c54942ba237f8ec0f891"

    n = 50

    year = 2016
    doctype = "bk"

    # where to save the results
    dname_book_count = os.path.join(BASE_DIR, "data", "aff_book_{}".format(year))

    col_dict = {2012: "book_downloaded_2012",
                2013: "book_downloaded_2013",
                2014: "book_downloaded_2014",
                2015: "book_downloaded_2015",
                2016: "book_downloaded_2016"}


    fname_long_book = 'data/long_book_count.csv'

    try:
        df_old = pd.read_csv(fname_long_book)
    except:
        df_old = pd.DataFrame(columns=['name', 'metricType', 'year', 'valueByYear'])


    for i in range(n):

        logger.debug("getting univerity name")
        aff_name = df_aff.next_aff(col_dict[year])
        logger.debug("university name is {}".format(aff_name))

        logger.debug("creating query")
        query = scopus_query(year=year, doctype=doctype, affil='{}'.format(aff_name)).encode().set_query().get_query()

        logger.debug("query is {}".format(query))

        logger.debug("sending the request")

        fname_jres = os.path.join(dname_book_count, "{}_year_{}.json".format(aff_name.title().replace(" ", ""), year))

        try:
            res = my_scopus_search(query=query, apiKey=MY_API_KEY)

            s = res.get_search_object()

            q = {'name': aff_name,
                 'metricType': 'BookCount',
                 'year': year,
                 'valueByYear': s['search-results']['opensearch:totalResults']}

            df_old = df_old.append(q, ignore_index=True)


            logger.debug("respond received sucessfuly")

            logger.debug('saving the response to {}'.format(fname_jres))
            with open(fname_jres, "w") as f:
                json.dump(s, f)

            logger.debug("json file saved successfully")

            logger.debug("update the file")

            df_af.at[aff_name, col_dict[year]] = 1

        except Exception as e:

            if res.http_error == 401:
                logger.debug("error retrieved, error is {}".format(res.http_error))
            elif res.http_error == 429:
                logger.info("quota is exceeded, terminating the program")
                break
            else:
                logger.debug("error retrieved, error is {}".format(res.http_error))
                df_af.at[aff_name, col_dict[year]] = -1

            logger.warn('respond has failed, error is ', e)

    try:
        logger.debug("saving the updated table")
        df_af.to_csv(fname_aff_book_count)
        logger.debug("table was updated successfully")
    except Exception as e:
        logger.warn("saving updated talbe has failed, please, save the table manually")


    df_old.to_csv(fname_long_book, index=False)
