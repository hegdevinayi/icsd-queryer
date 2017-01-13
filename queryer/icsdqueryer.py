import sys
import os
import json
from selenium import webdriver
from tags import ICSD_QUERY_TAGS, ICSD_PARSE_TAGS

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
                values. Currently supported field names:
                1. composition
                2. number_of_elements
                3. icsd_collection_code
                E.g., {'composition': 'Ni:2:2 Ti:1:1', 'number_of_elements': 2}
                [Note]: the field names must exactly match the ones listed above
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
            element_id = ICSD_QUERY_TAGS[k]
            self.driver.find_element_by_id(element_id).send_keys(v)

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

    # panel: "Summary"
    def get_PDF_number(self):
        pdf_number = ""
        tag = ICSD_PARSE_TAGS['PDF_number']
        xpath = "//*[text()[contains(., '{}')]]/../td/div".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        if nodes[0].text != 'R-value':
            pdf_number = nodes[0].text.split('\n')[0]
        return pdf_number

    def get_authors(self):
        authors = ""
        tag = ICSD_PARSE_TAGS['authors']
        xpath = "//*[text()[contains(., '{}')]]/../td".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        authors = nodes[1].text.strip().replace('\n', ' ')
        return authors

    def get_publication_title(self):
        element = self.driver.find_element_by_id('textfield13')
        return element.text.strip().replace('\n', ' ')

    def get_reference(self):
        element = self.driver.find_element_by_id('textfield12')
        return element.text.strip().replace('\n', ' ')

    # panel: "Chemistry"
    def get_chemical_formula(self):
        element = self.driver.find_element_by_id('textfieldChem1')
        return element.get_attribute('value').strip()

    def get_structural_formula(self):
        element = self.driver.find_element_by_id('textfieldChem3')
        return element.text.strip()

    def get_AB_formula(self):
        element = self.driver.find_element_by_id('textfieldChem6')
        return element.get_attribute('value').strip()

    # panel: "Published Crystal Structure Data"
    def get_cell_parameters(self):
        element = self.driver.find_element_by_id('textfieldPub1')
        raw_text = element.get_attribute('value').strip()
        a, b, c, alpha, beta, gamma = [ float(e.split('(')[0]) for e in
                                       raw_text.split() ]
        cell_parameters = {'a': a, 'b': b, 'c': c, 'alpha': alpha, 'beta': beta,
                           'gamma': gamma}
        return cell_parameters

    def get_volume(self):
        element = self.driver.find_element_by_id('textfieldPub2')
        return float(element.get_attribute('value').strip())

    def get_space_group(self):
        element = self.driver.find_element_by_id('textfieldPub5')
        return element.get_attribute('value').strip()

    def get_crystal_system(self):
        element = self.driver.find_element_by_id('textfieldPub8')
        return element.get_attribute('value').strip()

    def get_wyckoff_sequence(self):
        element = self.driver.find_element_by_id('textfieldPub11')
        return element.get_attribute('value').strip()

    def get_formula_units_per_cell(self):
        element = self.driver.find_element_by_id('textfieldPub3')
        return int(element.get_attribute('value').strip())

    def get_pearson(self):
        element = self.driver.find_element_by_id('textfieldPub6')
        return element.get_attribute('value').strip()

    def get_crystal_class(self):
        element = self.driver.find_element_by_id('textfieldPub9')
        return element.get_attribute('value').strip()

    def get_structural_prototype(self):
        element = self.driver.find_element_by_id('textfieldPub12')
        return element.get_attribute('value').strip()

    # panel: "Bibliography"
    def _get_references(self, n):
        tag = 'Reference'
        xpath = "//*[text()[contains(., '{}')]]/../td/div".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        reference = self._clean_reference_string(nodes[n].text)
        return reference

    def get_reference_1(self):
        return self._get_references(0)

    def get_reference_2(self):
        return self._get_references(1)

    def get_reference_3(self):
        return self._get_references(2)

    def _clean_reference_string(self, r):
        r = r.strip()
        r = r.replace('Northwestern University Library', '').strip()
        r = r.replace('\n', ' ')
        return r

    # panel: "Warnings & Comments"
    def get_warnings(self):
        warnings = []
        block_element = self.driver.find_element_by_id('ir_a_8_81a3e')
        warning_nodes = block_element.find_elements_by_xpath(".//table/tbody/tr")
        for node in warning_nodes:
            if node.text:
                warnings.append(node.text.strip().replace('\n', ' '))
        return warnings

    def get_comments(self):
        comments = []
        block_element = self.driver.find_element_by_id('ir_a_8_81a3e')
        tag = ICSD_PARSE_TAGS['comments']
        xpath = ".//*[text()[contains(., '{}')]]/../../div/div/div".format(tag)
        comment_nodes = block_element.find_elements_by_xpath(xpath)
        for node in comment_nodes:
            if node.text:
                comments.append(node.text.strip().replace('\n', ' '))
        return comments

    # panel: "Experimental Conditions"
    # text fields
    def get_temperature(self):
        temperature = ""
        tag = ICSD_PARSE_TAGS['temperature']
        xpath = "//*[text()[contains(., '{}')]]/../../td/input".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        temperature = nodes[0].get_attribute('value').strip()
        return temperature

    def get_pressure(self):
        pressure = ""
        tag = ICSD_PARSE_TAGS['pressure']
        xpath = "//*[text()[contains(., '{}')]]/../../td/input".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        pressure = nodes[1].get_attribute('value').strip()
        return pressure

    def get_R_value(self):
        R_value = ""
        tag = ICSD_PARSE_TAGS['R_value']
        xpath = "//*[text()[contains(., '{}')]]".format(tag)
        xpath += "/../td/input[@type='text']"
        node = self.driver.find_element_by_xpath(xpath)
        R_value = node.get_attribute('value').strip()
        if R_value:
            R_value = float(R_value)
        return R_value

    # checkboxes
    def _is_checkbox_enabled(self, tag_key):
        tag = ICSD_PARSE_TAGS[tag_key]
        xpath = "//*[text()[contains(., '{}')]]".format(tag)
        xpath += "/../input[@type='checkbox']"
        node = self.driver.find_element_by_xpath(xpath)
        if node.get_attribute('checked') is None:
            return False
        else:
            return True

    def is_x_ray(self):
        return self._is_checkbox_enabled('x_ray')

    def is_electron_diffraction(self):
        return self._is_checkbox_enabled('electron_diffraction')

    def is_neutron_diffraction(self):
        return self._is_checkbox_enabled('neutron_diffraction')

    def is_synchrotron(self):
        return self._is_checkbox_enabled('synchrotron')

    def is_powder(self):
        return self._is_checkbox_enabled('powder')

    def is_single_crystal(self):
        return self._is_checkbox_enabled('single_crystal')

    def is_twinned_crystal_data(self):
        return self._is_checkbox_enabled('twinned_crystal_data')

    def is_rietveld_employed(self):
        return self._is_checkbox_enabled('rietveld_employed')

    def is_absolute_config_determined(self):
        return self._is_checkbox_enabled('absolute_config_determined')

    def is_theoretical_calculation(self):
        return self._is_checkbox_enabled('theoretical_calculation')

    def is_magnetic_structure_available(self):
        return self._is_checkbox_enabled('magnetic_structure_available')

    def is_anharmonic_temperature_factors_given(self):
        return self._is_checkbox_enabled('anharmonic_temperature_factors_given')

    def is_NMR_data_available(self):
        return self._is_checkbox_enabled('NMR_data_available')

    def is_correction_of_previous(self):
        return self._is_checkbox_enabled('correction_of_previous')

    def is_polytype(self):
        return self._is_checkbox_enabled('polytype')

    def is_order_disorder(self):
        return self._is_checkbox_enabled('order_disorder')

    def is_disordered(self):
        return self._is_checkbox_enabled('disordered')

    def is_defect(self):
        return self._is_checkbox_enabled('defect')

    def is_misfit_layer(self):
        return self._is_checkbox_enabled('misfit_layer')

    def is_mineral(self):
        return self._is_checkbox_enabled('mineral')

    def is_is_prototype_structure(self):
        return self._is_checkbox_enabled('is_prototype_structure')


    def parse_data(self):
        """
        get all the information for the entry
        """
        json = {}
        json['collection_code'] = self.get_collection_code()
        for tag in ICSD_PARSE_TAGS.keys():
            # assume text field
            method = 'get_{}'.format(tag)
            try:
                json[tag] = getattr(self, method)()
            except AttributeError:
                pass
            else:
                continue

            # assume checkbox
            method = 'is_{}'.format(tag)
            try:
                json[tag] = getattr(self, method)()
            except AttributeError:
                ##sys.stdout.write('"{}" parser not implemented!\n'.format(tag))
                continue

        for tag in json.keys():
            sys.stdout.write('{}: {}\n'.format(tag, json[tag]))

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

    def quit(self):
        self.driver.quit()
