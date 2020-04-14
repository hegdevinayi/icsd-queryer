import os
import shutil
import json
import time
from logging import getLogger
from logging import StreamHandler
from logging import FileHandler
from logging import NullHandler

from selenium import webdriver

from tags import ICSD_QUERY_TAGS, ICSD_PARSE_TAGS


logger = getLogger(__name__)


class QueryerError(Exception):
    pass


class Queryer(object):
    """
    Base class to query the ICSD via the web interface using a Selenium
    WebDriver (http://selenium-python.readthedocs.io/).
    """

    def __init__(self,
                 url=None,
                 use_login=None,
                 userid=None,
                 password=None,
                 query=None,
                 save_screenshot=None,
                 structure_sources=None,
                 log_stream=None):
        """
        Initialize the webdriver and load the URL.
        (Also, check if the "Basic Search" page has loaded successfully.)

        **[Note 1]**: Only ChromeDriver has been implemented.
        **[Note 2]**: Only the 'Basic Search & Retrieve' form is implemented.

        Keyword arguments:
            url:
                URL of the ICSD web search page.

                Default: https://icsd.fiz-karlsruhe.de/search/basic.xhtml.

            use_login:
                Boolean specifying whether user login needs to be used or not.

                Default: False.

            userid:
                User ID of the account used to login to the web page.

                Default: None.
                    - If `use_login` is True, and no user ID is specified, an
                    environment variable `ICSD_USERID` is looked for.
                    - If `use_login` is False, IP-based authentication is
                    assumed.

            password:
                Password of the user account used to login to the web page.

                Default: None.
                    - If `use_login` is True, and no password is specified, an
                    environment variable `ICSD_PASSWORD` is looked for.
                    - If `use_login` is False, IP-based authentication is
                    assumed.

            query:
                The query to be posted to the webform -- a dictionary of field
                names as keys and what to fill in them as the corresponding
                values.

                Currently supported field names:
                1. "composition"
                2. "number_of_elements"
                3. "icsd_collection_code"
                E.g., {'composition': 'Ni:2:2 Ti:1:1', 'number_of_elements': 2}

                **[Note]**: field names must *exactly* match the ones
                listed above.

            save_screenshot:
                Boolean specifying whether a screenshot of the ICSD web page
                should be saved locally?
                (Default: False)

            structure_sources:
                List of strings specifying whether the search should be limited
                to one of the below or a combination thereof:
                    1. "expt" = Experimental inorganic structures
                    2. "mofs" = Experimental metal-organic structures
                    3. "theo" = Theoretical structures
                These options correspond to the checkboxes available on the
                "Content Selection" panel on the left in the ICSD Web Search
                page.

                For example, ["expt"] queries for only experimental inorganic
                structures, ["mofs"] queries for only experimental
                metal-organic structures, ["expt", "theo"] queries for
                experimental inorganic AND theoretical structures, and so on.

                Default: ["expt"]

            log_stream:
                String with the path to a file where logs should be written,
                or alternatively "console" (case-insensitive) to write logs to
                the console (standard output/error stream).
                An additional option of "nolog" can be specified to avoid all
                logging.

                Default: "console".

        Attributes:
            url: URL of the search page
            query: query to be posted to the webform
            save_screenshot: whether to take a screenshot of the ICSD page
            structure_sources: which structure sources to search for
            browser_data_dir: directory for browser user profile, related data
            driver: instance of Selenium WebDriver running PhantomJS
            hits: number of search hits for the query

        """
        self._url = None
        self.url = url

        self._use_login = None
        self.use_login = use_login

        self._userid = None
        self.userid = userid

        self._password = None
        self.password = password

        self._query = None
        self.query = query

        self._save_screenshot = None
        self.save_screenshot = save_screenshot

        self._structure_sources = None
        self.structure_sources = structure_sources

        self._log_stream = None
        self.log_stream = log_stream
        self.add_log_handlers()

        self.driver = self._initialize_driver()
        self.load_web_search()

        self.hits = 0

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        if not url:
            url = 'https://icsd.fiz-karlsruhe.de/search/basic.xhtml'
        self._url = url

    @property
    def use_login(self):
        return self._use_login

    @use_login.setter
    def use_login(self, use_login):
        if use_login is None:
            self._use_login = False
        elif isinstance(use_login, str):
            self._use_login = use_login.lower()[0] == 't'
        else:
            self._use_login = use_login

    @property
    def userid(self):
        return self._userid

    @userid.setter
    def userid(self, userid):
        if userid is not None:
            self._userid = userid
        elif os.environ.get('ICSD_USERID') is not None:
            self._userid = os.environ.get('ICSD_USERID')

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if password is not None:
            self._password = password
        elif os.environ.get('ICSD_PASSWORD') is not None:
            self._password = os.environ.get('ICSD_PASSWORD')

    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, query):
        if not query:
            self._query = {}
        else:
            self._query = query

    @property
    def save_screenshot(self):
        return self._save_screenshot

    @save_screenshot.setter
    def save_screenshot(self, save_screenshot):
        if save_screenshot is None:
            self._save_screenshot = False
        elif isinstance(save_screenshot, str):
            self._save_screenshot = save_screenshot.lower()[0] == 't'
        else:
            self._save_screenshot = save_screenshot

    @property
    def structure_sources(self):
        return self._structure_sources

    @structure_sources.setter
    def structure_sources(self, structure_sources):
        if not structure_sources:
            self._structure_sources = ['e']
        else:
            self._structure_sources = []
            for s in structure_sources:
                self._structure_sources.append(s.lower()[0])

    @property
    def log_stream(self):
        return self._log_stream

    @log_stream.setter
    def log_stream(self, log_stream):
        if log_stream is None:
            log_stream = "console"
        self._log_stream = log_stream

    def add_log_handlers(self):
        if self._log_stream.lower() == 'nolog':
            logger.addHandler(NullHandler)
        if self._log_stream.lower() == 'console' or self._log_stream is None:
            std_stream = StreamHandler()
            logger.addHandler(std_stream)
        else:
            file_stream = FileHandler(self._log_stream)
            logger.addHandler(file_stream)

    def _initialize_driver(self):
        browser_data_dir = os.path.join(os.getcwd(), 'browser_data')
        if os.path.exists(browser_data_dir):
            shutil.rmtree(browser_data_dir, ignore_errors=True)
        self.download_dir = os.path.abspath(os.path.join(browser_data_dir,
                                                         'driver_downloads'))
        logger.info('Starting a ChromeDriver ')
        logger.info('with the default download directory:')
        logger.info(' "{}"'.format(self.download_dir))
        _options = webdriver.ChromeOptions()
        # using to --no-startup-window to run Chrome in the background throws a
        # WebDriver.Exception with "Message: unknown error: Chrome failed to
        # start: exited normally"
        ##_options.add_argument('--no-startup-window ')
        _options.add_argument('user-data-dir={}'.format(browser_data_dir))
        prefs = {'download.default_directory': self.download_dir}
        _options.add_experimental_option("prefs", prefs)
        return webdriver.Chrome(chrome_options=_options)

    def load_web_search(self):
        self.load_url()
        if self._use_login:
            self.login_personal()
        self._check_basic_search()

    def load_url(self):
        """
        Loads the specified URL and checks if the "Basic Search & Retrieve"
        interface has been successfully loaded.
        """
        self.driver.get(self.url)
        self.driver.implicitly_wait(1.0)

    def login_personal(self):
        if self.userid is None:
            return
        # enter the user id
        userid_field_id = 'content_form:loginId'
        userid_field = self.driver.find_element_by_id(userid_field_id)
        userid_field.send_keys(self.userid)
        # enter the password
        passwd_field_id = 'content_form:password'
        passwd_field = self.driver.find_element_by_id(passwd_field_id)
        passwd_field.send_keys(self.password)
        # click the login button
        login_button_id = 'content_form:loginButtonPersonal'
        login_button = self.driver.find_element_by_id(login_button_id)
        login_button.click()

    def _check_basic_search(self):
        """
        Use By.ID to locate the Search Panel header element; if 'Basic Search'
        is not in the element text, raise Error.
        """
        header_id = 'content_form:mainSearchPanel_header'
        try:
            header = self.driver.find_element_by_id(header_id)
        except:
            self.quit()
            error_message = 'Failed to load Basic Search & Retrieve'
            raise QueryerError(error_message)
        else:
            if 'Basic Search' not in header.text:
                self.quit()
                error_message = 'Failed to load Basic Search & Retrieve'
                raise QueryerError(error_message)

    def select_structure_sources(self):
        """
        Select the appropriate checkbox in the "Content Selection" panel (in
        a menu on the left of the main page) based on the specified strucure
        sources.

        By default, the "Experim. inorganic structures" checkbox is selected,
        so click appropriately.

        """
        labels = {
            'e': [0, 'Experim. inorganic'],
            'm': [1, 'Experim. metal-organic'],
            't': [2, 'Theoretical']
        }
        for label in labels:
            xpath = "//tbody/tr/td/label[text()[contains(., '{}')]]".format(
                labels[label][1])
            clickable_elem = self.driver.find_element_by_xpath(xpath)
            checkbox = self.driver.find_element_by_id(
                'content_form:uiSelectContent:{}'.format(labels[label][0]))
            if label in self.structure_sources:
                if not checkbox.is_selected():
                    clickable_elem.click()
                    time.sleep(5.0)
            elif label not in self.structure_sources:
                if checkbox.is_selected():
                    clickable_elem.click()
                    time.sleep(5.0)

    def post_query_to_form(self):
        """
        Use By.ID to locate elements in the query (using IDs stored in
        `tags.ICSD_QUERY_TAGS`), POST keys to the form in the URL `self.url`,
        and run the query.
        (Also check if the 'List View' page has been loaded successfully.)
        """
        if not self.query:
            self.quit()
            error_message = 'Empty query'
            raise QueryerError(error_message)

        logger.info('Querying the ICSD for')
        for k, v in self.query.items():
            element_id = ICSD_QUERY_TAGS[k]
            self.driver.find_element_by_id(element_id).send_keys(v)
            logger.info('\t{} = "{}"'.format(k, v))
        logger.flush()

        self._run_query()

    def _run_query(self):
        """
        Use By.NAME to locate the 'Run Query' button and click it.
        """
        self.driver.find_element_by_name('content_form:btnRunQuery').click()

    def _check_list_view(self):
        """
        Use By.CLASS_NAME to locate the first 'title' element, raise Error if
        'List View' is not in the element text.
        Parse element text to get number of hits for the current query
        (last item when text is split), assign to `self.hits`.
        """
        time.sleep(2.0)
        pop = self.driver.find_element_by_id('content_form:messages_container')
        if 'No results found' in pop.text:
            return

        titles = self.driver.find_elements_by_class_name('ui-panel-title')
        list_view_loaded = any(['List View' in t.text for t in titles])
        if not list_view_loaded:
            error_message = 'Failed to load "List View" of results'
            raise QueryerError(error_message)
        else:
            for title in titles:
                if 'List View' in title.text:
                    self.hits = int(title.text.split()[-1])
                    break

    def _click_select_all(self):
        """
        Use By.ID to locate the 'Select All' button, and click it.
        """
        time.sleep(1.0)
        self.driver.find_element_by_id(
            'display_form:listViewTable:uiSelectAllRows').click()

    def _click_show_detailed_view(self):
        """
        Use By.ID to locate the 'Show Detailed View' button, and click it.
        """
        time.sleep(1.0)
        self.driver.find_element_by_id(
            'display_form:btnEntryViewDetailed').click()
        self._check_detailed_view()
        self._expand_all()

    def _check_detailed_view(self):
        """
        Use By.CLASS_NAME to locate the 'title' element, and verify that the
        "Detailed View" page is loaded as expected.
        """
        if 'Details on Search Result' in self.driver.title:
            return
        try:
            title = self.driver.find_element_by_class_name('ui-panel-title')
        except:
            error_message = 'Failed to load "Detailed View" of results'
            raise QueryerError(error_message)

        else:
            if 'Detailed View' not in title.text:
                self.quit()
                error_message = 'Failed to load "Detailed View" of results'
                raise QueryerError(error_message)

    def _expand_all(self):
        """
        Use By.ID to locate the 'Expand All' button, and click it.
        """
        time.sleep(1.0)
        self.driver.find_element_by_id('display_form:expandAllButton').click()

    def _get_number_of_entries_loaded(self):
        """
        Use By.CLASS_NAME to locate 'title' elements, split the element text
        with 'Detailed View' in it and return the last item in the list.
        """
        titles = self.driver.find_elements_by_class_name('ui-panel-title')
        for title in titles:
            if 'Detailed View' in title.text:
                n_entries_loaded = int(title.text.split()[-1])
                return n_entries_loaded

    def parse_entries(self):
        """
        Parse all entries resulting from the query.

        If the number of entries loaded is equal to `self.hits`, raise Error.
        Loop through all the entries loaded, and for each entry:
            a. create a directory named after its ICSD Collection Code
            b. write "meta_data.json" into the directory
            c. save "screenshot.png" into the directory
            d. export the CIF into the directory
        Close the browser session and quit.

        Return: (list) A list of ICSD Collection Codes of entries parsed

        """
        entries_parsed = []

        self._check_list_view()
        logger.info('The query yielded {} hits.'.format(self.hits))
        logger.flush()
        if self.hits == 0:
            return entries_parsed

        self._click_select_all()
        self._click_show_detailed_view()

        if self._get_number_of_entries_loaded() != self.hits:
            self.quit()
            error_message = '# Hits != # Entries in Detailed View'
            raise QueryerError(error_message)

        logger.info('Parsing all the entries...')
        logger.flush()
        for i in range(self.hits):
            # get entry data
            entry_data = self.parse_entry()

            # create a directory for the entry after the ICSD Collection Code
            coll_code = str(entry_data['collection_code'])
            if os.path.exists(coll_code):
                shutil.rmtree(coll_code)
            os.mkdir(coll_code)

            # write the parsed data into a JSON file in the directory
            json_file = os.path.join(coll_code, 'metadata.json')
            with open(json_file, 'w') as fw:
                json.dump(entry_data, fw, indent=2)

            # save the screenshot the current page into the directory
            if self.save_screenshot:
                screenshot_file = os.path.join(coll_code, 'screenshot.png')
                self.save_screenshot(fname=screenshot_file)

            # get the CIF file
            self.export_cif()
            # uncomment the next few lines for automatic copying of CIF files
            # into the correct folders
            # wait for the file download to be completed
            cif_name = 'ICSD_CollCode{}.cif'.format(coll_code)
            cif_source_loc = os.path.join(self.download_dir, cif_name)
            while True:
                if os.path.exists(cif_source_loc):
                    break
                else:
                    time.sleep(1.0)
            # move it into the directory of the current entry
            cif_dest_loc = os.path.join(coll_code, '{}.cif'.format(coll_code))
            shutil.move(cif_source_loc, cif_dest_loc)

            logger.info('[{}/{}]: '.format(i+1, self.hits))
            logger.info('Data exported into folder:')
            logger.info('"{}"'.format(coll_code))
            logger.flush()
            entries_parsed.append(coll_code)

            if i < (self.hits - 1):
                self._go_to_next_entry()

        logger.info('Closing the browser session and exiting.')
        logger.flush()
        self.quit()
        return entries_parsed

    def _go_to_next_entry(self):
        """
        Use By.ID to locate the 'Next' button, and click it.
        """
        time.sleep(1.0)
        self.driver.find_element_by_id('display_form:buttonNext').click()

    def parse_entry(self):
        """
        Parse all `tags.ICSD_PARSE_TAGS` + the ICSD Collection Code for the
        current entry, and construct a dictionary `parsed_data` with tag:value.

        Return: (dict) `parsed_data` with [tag]:[parsed value]
        """
        time.sleep(1.0)
        parsed_data = {}
        parsed_data['collection_code'] = self.get_collection_code()
        for tag in ICSD_PARSE_TAGS.keys():
            parsed_data[tag] = self.parse_property(tag)
        return parsed_data

    def get_collection_code(self):
        """
        Use By.CLASS_NAME to locate 'title' elements, parse the ICSD Collection
        Code from the element text and raise Error if unsuccessful.

        Return: (integer) ICSD Collection Code
        """
        titles = self.driver.find_elements_by_class_name('ui-panel-title')
        for title in titles:
            if 'Summary' in title.text:
                try:
                    return int(title.text.split()[-1])
                except:
                    self.quit()
                    error_message = 'Failed to parse the ICSD Collection Code'
                    raise QueryerError(error_message)

    def parse_property(self, tag=None):
        """
        Parse the value in the field specified by `tag`.

        For tags "remarks", "calculation_method", "keywords", "comments", and
        "warnings", a list of field values are returned. For all other tags, a
        single string (empty string if property not available) is returned.

        """
        if not tag:
            return
        if tag in ['remarks', 'calculation_method', 'keywords', 'comments',
                   'warnings']:
            return self.parse_property_list(tag)

        search_text = ICSD_PARSE_TAGS[tag]
        xpath = "//td[text()[contains(., '{}')]]/../td".format(search_text)
        td_elements = self.driver.find_elements_by_xpath(xpath)
        if not td_elements:
            return ""
        for i in reversed(range(len(td_elements))):
            if 'outputlabel' not in td_elements[i].get_attribute('class'):
                continue
            if td_elements[i].text == search_text:
                return td_elements[i+1].text.strip()

    def parse_property_list(self, tag=None):
        """
        Parse the value in the fields specified by `tag` and return as a list.
        """
        if not tag:
            return
        values = set()
        search_text = ICSD_PARSE_TAGS[tag]
        xpath = "//td[text()[contains(., '{}')]]/../td".format(search_text)
        td_elements = self.driver.find_elements_by_xpath(xpath)
        if td_elements:
            for i in range(len(td_elements)):
                if td_elements[i].text == search_text:
                    value = td_elements[i+1].text.strip()
                    if not value:
                        continue
                    values.add(value)
        return list(values)

    def export_cif(self):
        """
        Use By.ID to locate the 'Export Cif' button and click it. The file is
        downloaded as "ICSD_CollCode[icsd_id].cif" into the download directory
        specified for the webdriver.

        """
        self.driver.find_element_by_id(
            'display_form:btnEntryDownloadCif').click()

    def save_screenshot(self, size=None, fname='ICSD.png'):
        """
        Save screenshot of the current page.

        Keyword arguments:
            size: (default: None)
                tuple (width, height) of the current window

            fname: (default: 'ICSD.png')
                save screenshot into this file
        """
        if size:
            self.driver.set_window_size(size[0], size[1])
        self.driver.save_screenshot(fname)

    def quit(self):
        self.driver.stop_client()
        self.driver.quit()

    def perform_icsd_query(self):
        """
        Post the query to form, parse data for all the entries. (wrapper)
        """
        try:
            self.select_structure_sources()
            self.post_query_to_form()
            self.parse_entries()
        finally:
            time.sleep(1.0)
            self.quit()
