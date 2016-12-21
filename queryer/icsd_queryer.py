from selenium import webdriver
from bs4 import BeautifulSoup

class ICSDQueryer():
    """
    class to query the ICSD for data
    """

    def __init__(self):
        self.driver = webdriver.PhantomJS()

    def save_screenshot(self, window_size=(1600,900), filename='ICSD_Screenshot.png'):
        self.driver.set_window_size(window_size)
        self.driver.save_screenshot(filename)

    def get_url_request(self, url):
        return self.driver.get(url)

    def run_query(self):
        self.driver.find_element_by_name('content_form:btnRunQuery').click()

    def perform_query(self, query):
        for k, v in query.items():
            self.driver.find_element_by_id(v[0]).send_keys(v[1])
        self.run_query()

    def click_select_all(self):
        self.driver.find_element_by_id('LV_Select').click()

    def click_detailed_view(self):
        self.driver.find_element_by_id('LV_Detailed').click()
        self.expand_all()

    def expand_all_dropdown(self):
        self.driver.find_element_by_css_selector('a#ExpandAll.no_print').click()

    def export_cif_file(self, base_filename='ICSD_Coll_Code'):
        self.driver.find_element_by_id('fileNameForExportToCif').send_keys(base_filename)
        self.driver.find_element_by_id('aExportCifFile').click()

