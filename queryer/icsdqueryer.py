import sys
import os
import json
from selenium import webdriver

class Error(Exception):
    pass

class Queryer:
    """
    Base class to query the ICSD using the web interface via the Selenium
    webdriver.

    functions:
        post_query_to_form
        parse_data
            save_CIF
            get_metadata
            save_screenshot
    """

    _url = 'https://icsd.fiz-karlsruhe.de/search/basic.xhtml'
    _query = {}
    def __init__(self, url=_url, query=_query):
        """
        Initialize the webdriver and load the URL.
        [Note1]: Only PhantomJS browser has been implemented.
        [Note2]: Only the 'Basic Search & Retrieve' form has been implemented.

        Keyword arguments:
            url:
                URL of the search page (currently on the basic page is
                implemented)

            query:
                the query to be posted to the webform -- a dictionary of field
                names as keys and what to fill in them as the corresponding
                values, e.g., {'composition': 'Ni:2:2 Ti:1:1',
                'number_of_elements': 2} [Note]: the field names must exactly
                match the ones on the web page, but in lower case, spaces
                replaced by underscores. In the above example, the field name
                visible on the form is "Number of Elements".
        """
        self.url = url
        self.query = query
        self.driver = webdriver.PhantomJS()
        self.driver.get(self.url)
        self._check_basic_search()
        self.hits = 0

    def _check_basic_search(self):
        header_id = 'content_form:mainSearchPanel_header'
        header = self.driver.find_element_by_id(header_id)
        if 'Basic Search' not in header.text:
            error_message = 'Unable to load Basic Search & Retrieve'
            raise Error(error_message)

    def post_query_to_form(self):
        """
        post query "self.query" to the form in the URL self.url
        """
        if not self.query:
            error_message = "Empty query"
            raise Error(error_message)

        for k, v in self.query.items():
            self.driver.find_element_by_id(v[0]).send_keys(v[1])

        self._run_query()
        self._check_list_view()

    def _run_query(self):
        self.driver.find_element_by_name('content_form:btnRunQuery').click()

    def _check_list_view(self):
        title = self.driver.find_element_by_class_name('title')
        if 'List View' not in title.text:
            error_message = 'Unable to load List View of results'
            raise Error(error_message)
        self.hits = int(title.text.split()[-1])

    def _click_select_all(self):
        self.driver.find_element_by_id('LVSelect').click()

    def _click_detailed_view(self):
        self.driver.find_element_by_id('LVDetailed').click()
        self._check_detailed_view()
        self._expand_all()

    def _check_detailed_view(self):
        titles = self.driver.find_elements_by_class_name('title')
        detailed_view = False
        for title in titles:
            if 'Detailed View' in title.text:
                # also check if the number of entries loaded is consistent with
                # the number of the hits obtained for the search
                n_entries_loaded = int(title.text.split()[-1])
                if n_entries_loaded != self.hits:
                    error_message = '# Hits != Entries loaded in Detailed View'
                    raise Error(error_message)
                else:
                    detailed_view = True
                    break
        if not detailed_view:
            error_message = 'Unable load Detailed View of results'
            raise Error(error_message)

    def _expand_all(self):
        self.driver.find_element_by_css_selector('a#ExpandAll.no_print').click()

    def get_collection_code(self):
        collection_code = None
        titles = self.driver.find_elements_by_class_name('title')
        for title in titles:
            if 'Summary' in title.text:
                collection_code = int(title.text.split()[-1])
                break
        return collection_code

    def parse_data(self):
        """
        get all the information for the entry
        """
        json = {}
        json['coll_code'] = self.get_collection_code()
        print json['coll_code']
        labels = self.driver.find_elements_by_class_name('label')
        for l in labels:
            print l.text

    def export_cif_file(self, base_filename='ICSD_Coll_Code'):
        self.driver.find_element_by_id('fileNameForExportToCif').send_keys(base_filename)
        self.driver.find_element_by_id('aExportCifFile').click()

    def save_screenshot(self, size=(1600,900), fname='ICSD.png'):
        """
        Keyword arguments:
            size:
                tuple (width, height) of the current window
                default = (1600,900)

            fname:
                save screenshot into this file
                default = 'ICSD.png'
        """
        self.driver.set_window_size(size[0], size[1])
        self.driver.save_screenshot(fname)


