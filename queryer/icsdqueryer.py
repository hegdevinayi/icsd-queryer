import sys
import os
import shutil
import json
import time
from selenium import webdriver
from tags import ICSD_QUERY_TAGS, ICSD_PARSE_TAGS

class Error(Exception):
    pass

class Queryer:
    """
    Base class to query the ICSD via the web interface using a Selenium
    WebDriver (http://selenium-python.readthedocs.io/).

    Methods:
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
        (Also, check if the "Basic Search" page has loaded successfully.)

        **[Note1]**: Only ChromeDriver has been implemented.
        **[Note2]**: Only the 'Basic Search & Retrieve' form has been implemented.

        Keyword arguments:
            url:
                URL of the search page

            query:
                the query to be posted to the webform -- a dictionary of field
                names as keys and what to fill in them as the corresponding
                values. Currently supported field names:
                1. composition
                2. number_of_elements
                3. icsd_collection_code
                E.g., {'composition': 'Ni:2:2 Ti:1:1', 'number_of_elements': 2}
                **[Note]**: field names must _exactly_ match those listed above!

        Attributes:
            url: URL of the search page
            query: query to be posted to the webform (see kwargs)
            browser_data_dir: directory for browser user profile, related data
            driver: instance of Selenium WebDriver running PhantomJS
            hits: number of search hits for the query
        """
        self.url = url
        self.query = query
        sys.stdout.write('Initializing a WebDriver...\n')
        sys.stdout.flush()
        self.driver = self._initialize_driver()
        sys.stdout.write('done.\n')
        sys.stdout.flush()
        sys.stdout.write('Loading {}... '.format(self.url))
        sys.stdout.flush()
        self.driver.get(self.url)
        sys.stdout.write('done.\n')
        self._check_basic_search()
        self.hits = 0

    def _initialize_driver(self):
        browser_data_dir = os.path.join(os.getcwd(), 'browser_data')
        if os.path.exists(browser_data_dir):
            shutil.rmtree(browser_data_dir)
        self.download_dir = os.path.abspath(os.path.join(browser_data_dir,
                                                         'driver_downloads'))
        sys.stdout.write('Starting a ChromeDriver ')
        sys.stdout.write('with the default download directory\n')
        sys.stdout.write('"{}"\n'.format(self.download_dir))
        sys.stdout.write('... ')
        _options = webdriver.ChromeOptions()
        _options.add_argument('user-data-dir={}'.format(browser_data_dir))
        prefs = {'download.default_directory': self.download_dir}
        _options.add_experimental_option("prefs", prefs)
        return webdriver.Chrome(chrome_options=_options)

    def _check_basic_search(self):
        """
        Use By.ID to locate the Search Panel header element; if 'Basic Search'
        is not in the element text, raise Error.
        """
        header_id = 'content_form:mainSearchPanel_header'
        header = self.driver.find_element_by_id(header_id)
        if 'Basic Search' not in header.text:
            error_message = 'Failed to load Basic Search & Retrieve'
            raise Error(error_message)

    def post_query_to_form(self):
        """
        Use By.ID to locate elements in the query (using IDs stored in
        `tags.ICSD_QUERY_TAGS`), POST keys to the form in the URL `self.url`,
        and run the query.
        (Also check if the 'List View' page has been loaded successfully.)
        """
        if not self.query:
            error_message = 'Empty query'
            raise Error(error_message)

        sys.stdout.write('Querying the ICSD for\n')
        for k, v in self.query.items():
            element_id = ICSD_QUERY_TAGS[k]
            self.driver.find_element_by_id(element_id).send_keys(v)
            sys.stdout.write('\t{} = "{}"\n'.format(k, v))
            sys.stdout.flush()

        self._run_query()
        self._check_list_view()

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
        title = self.driver.find_element_by_class_name('title')
        if 'List View' not in title.text:
            error_message = 'Failed to load "List View" of results'
            raise Error(error_message)
        try:
            self.hits = int(title.text.split()[-1])
        except TypeError:
            error_message= 'No hits/too many hits. Modify your query.'
            raise Error(error_message)
        else:
            sys.stdout.write('The query yielded {} hits.\n'.format(self.hits))
            sys.stdout.flush()

    def _click_select_all(self):
        """
        Use By.ID to locate the 'Select All' ('LVSelect') button, and click it.
        """
        self.driver.find_element_by_id('LVSelect').click()

    def _click_show_detailed_view(self):
        """
        Use By.ID to locate the 'Show Detailed View' ('LVDetailed') button, and
        click it.
        """
        self.driver.find_element_by_id('LVDetailed').click()
        self._check_detailed_view()
        self._expand_all()

    def _check_detailed_view(self):
        """
        Use By.ID to locate all 'title' elements. If none of the title texts
        have 'Detailed View', raise an Error.
        """
        titles = self.driver.find_elements_by_class_name('title')
        detailed_view = any(['Detailed View' in t.text for t in titles])
        if not detailed_view:
            error_message = 'Failed to load "Detailed View" of results'
            raise Error(error_message)

    def _expand_all(self):
        """
        Use By.CSS_SELECTOR to locate the 'Expand All' ('a#ExpandAll.no_print')
        button, and click it.
        """
        self.driver.find_element_by_css_selector('a#ExpandAll.no_print').click()

    def _get_number_of_entries_loaded(self):
        """
        Use By.CLASS_NAME to locate 'title' elements, split the element text
        with 'Detailed View' in it and return the last item in the list.
        """
        titles = self.driver.find_elements_by_class_name('title')
        for title in titles:
            if 'Detailed View' in title.text:
                n_entries_loaded = int(title.text.split()[-1])
                return n_entries_loaded

    def parse_entries(self):
        """
        Parse all entries resulting from the query.

        If the number of entries loaded is equal to `self.hits`, raise Error.
        Loop through all the entries loaded, and for each entry:
            (a) create a directory named after its ICSD Collection Code
            (b) write "meta_data.json" into the directory
            (c) save "screenshot.png" into the directory
            (d) export the CIF into the directory
        Close the browser session and quit.
        """
        if self._get_number_of_entries_loaded() != self.hits:
            error_message = '# Hits != # Entries in Detailed View'
            raise Error(error_message)

        sys.stdout.write('Parsing all the entries... \n')
        sys.stdout.flush()
        for i in range(self.hits):
            # get entry data
            entry_data = self.parse_entry()

            # create a directory for the entry after the ICSD Collection Code
            coll_code = str(entry_data['collection_code'])
            if os.path.exists(coll_code):
                shutil.rmtree(coll_code)
            os.mkdir(coll_code)

            # write the parsed data into a JSON file in the directory
            json_file = os.path.join(coll_code, 'meta_data.json')
            with open(json_file, 'w') as fw:
                json.dump(entry_data, fw)

            # save the screenshot the current page into the directory
            screenshot_file = os.path.join(coll_code, 'screenshot.png')
            self.save_screenshot(fname=screenshot_file)

            # get the CIF file
            self.export_CIF()
            # uncomment the next few lines for automatic copying of CIF files
            # into the correct folders
            # wait for the file download to be completed
            CIF_name = 'ICSD_Coll_Code_{}.cif'.format(coll_code)
            CIF_source_loc = os.path.join(self.download_dir, CIF_name)
            while True:
                if os.path.exists(CIF_source_loc):
                    break
                else:
                    time.sleep(0.1)
            # move it into the directory of the current entry
            CIF_dest_loc = os.path.join(coll_code, '{}.cif'.format(coll_code))
            shutil.move(CIF_source_loc, CIF_dest_loc)

            sys.stdout.write('[{}/{}]: '.format(i+1, self.hits))
            sys.stdout.write('Data exported into ')
            sys.stdout.write('folder "{}"\n'.format(coll_code))
            sys.stdout.flush()

            if self.hits != 1:
                self._go_to_next_entry()

        sys.stdout.write('Closing the browser session and exiting...')
        sys.stdout.flush()
        self.quit()
        sys.stdout.write(' done.\n')

    def _go_to_next_entry(self):
        """
        Use By.CLASS_NAME to locate the 'Next' button ('button_vcr_next'), and
        click it.
        """
        self.driver.find_element_by_class_name('button_vcr_next').click()

    def parse_entry(self):
        """
        Parse all `tags.ICSD_PARSE_TAGS` + the ICSD Collection Code for the
        current entry, and construct a dictionary `parsed_data` with tag:value.

        For each tag in `tags.ICSD_PARSE_TAGS`, call the method named
        `get_[tag]` or `is_[tag]` depending on whether the value to be parsed is
        a text field or checkbox, respectively, and raise an Error if the
        corresponding method is not found.

        Return: (dict) `parsed_data` with [tag]:[parsed value]
        """
        parsed_data = {}
        parsed_data['collection_code'] = self.get_collection_code()
        for tag in ICSD_PARSE_TAGS.keys():
            # assume text field
            method = 'get_{}'.format(tag)
            try:
                parsed_data[tag] = getattr(self, method)()
            except AttributeError:
                pass
            else:
                continue

            # assume checkbox
            method = 'is_{}'.format(tag)
            try:
                parsed_data[tag] = getattr(self, method)()
            except AttributeError:
                sys.stdout.write('"{}" parser not implemented!\n'.format(tag))
                continue
        return parsed_data

    def get_collection_code(self):
        """
        Use By.CLASS_NAME to locate 'title' elements, parse the ICSD Collection
        Code from the element text and raise Error if unsuccessful.

        Return: (integer) ICSD Collection Code
        """
        titles = self.driver.find_elements_by_class_name('title')
        for title in titles:
            if 'Summary' in title.text:
                try:
                    collection_code = int(title.text.split()[-1])
                    break
                except:
                    error_message = 'Failed to parse the ICSD Collection Code'
                    raise Error(error_message)
        return collection_code

    # panel: "Summary"
    def get_PDF_number(self):
        """
        Use By.XPATH to locate a 'td' node with the tag name (stored in
        `tags.ICSD_PARSE_TAGS`), parse the node text.

        Return: (string) PDF-number if available, empty string otherwise
        """
        pdf_number = ''
        tag = ICSD_PARSE_TAGS['PDF_number']
        xpath = "//td[text()[contains(., '{}')]]/../td/div".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        # if PDF_number field is empty, return "" instead of "R-value"
        if nodes[0].text != 'R-value':
            pdf_number = nodes[0].text.split('\n')[0]
        return pdf_number

    def get_authors(self):
        """
        Use By.XPATH to locate a 'td' node with the tag name (stored in
        `tags.ICSD_PARSE_TAGS`), parse the node text.

        Return: (string) Authors if available, empty string otherwise
        """
        authors = ''
        tag = ICSD_PARSE_TAGS['authors']
        xpath = "//td[text()[contains(., '{}')]]/../td".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        authors = nodes[1].text.strip().replace('\n', ' ')
        return authors

    def get_publication_title(self):
        """
        Use By.ID to locate 'Title of Article' ['textfield13'], parse the
        element text.

        Return: (string) Publication title if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfield13')
        return element.text.strip().replace('\n', ' ')

    def get_reference(self):
        """
        Use By.ID to locate 'Reference' for the publication ['textfield12'],
        parse the element text.

        Return: (string) Bibliographic reference if available, empty string
        otherwise
        """
        element = self.driver.find_element_by_id('textfield12')
        return element.text.strip().replace('\n', ' ')

    # panel: "Chemistry"
    def get_chemical_formula(self):
        """
        Use By.ID to locate 'Sum Form' ['textfieldChem1'], parse the elemnent
        text.

        Return: (string) Chemical formula if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldChem1')
        return element.get_attribute('value').strip()

    def get_structural_formula(self):
        """
        Use By.ID to locate 'Struct. Form.' ['textfieldChem3'], parse the
        element text.

        Return: (string) Structural formula if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldChem3')
        return element.text.strip()

    def get_AB_formula(self):
        """
        Use By.ID to locate 'AB Formula' ['textfieldChem6'], parse the element
        text.

        Return: (string) AB formula if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldChem6')
        return element.get_attribute('value').strip()

    # panel: "Published Crystal Structure Data"
    def get_cell_parameters(self):
        """
        Use By.ID to locate 'Cell Parameters' ['textfieldPub1'] textfield, get
        its 'value' attribute, strip uncertainties from the quantities, and
        construct a cell parameters dictionary.

        Return: (dictionary) Cell parameters with keys 'a', 'b', 'c', 'alpha',
                'beta', 'gamma', and values in float
                (Lattice vectors are in Angstrom, angles in degrees.)
        """
        element = self.driver.find_element_by_id('textfieldPub1')
        raw_text = element.get_attribute('value').strip()
        a, b, c, alpha, beta, gamma = [ float(e.split('(')[0]) for e in
                                       raw_text.split() ]
        cell_parameters = {'a': a, 'b': b, 'c': c, 'alpha': alpha, 'beta': beta,
                           'gamma': gamma}
        return cell_parameters

    def get_volume(self):
        """
        Use By.ID to locate 'Volume' ['textfieldPub2'], parse its 'value'
        attribute.

        Return: (float) Volume in cubic Angstrom
        """
        element = self.driver.find_element_by_id('textfieldPub2')
        return float(element.get_attribute('value').strip())

    def get_space_group(self):
        """
        Use By.ID to locate 'Space Group' ['textfieldPub5'], parse its 'value'
        attribute.

        Return: (string) Space group if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldPub5')
        return element.get_attribute('value').strip()

    def get_crystal_system(self):
        """
        Use By.ID to locate 'Crystal System' ['textfieldPub8'], parse its
        'value' attribute.

        Return: (string) Crystal system if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldPub8')
        return element.get_attribute('value').strip()

    def get_wyckoff_sequence(self):
        """
        Use By.ID to locate 'Wyckoff Sequence' ['textfieldPub11'], parse its
        'value' attribute.

        Return: (string) Wyckoff sequence if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldPub11')
        return element.get_attribute('value').strip()

    def get_formula_units_per_cell(self):
        """
        Use By.ID to locate 'Formula Units per Cell' ['textfieldPub3'], parse
        its 'value' attribute.

        Return: (integer) Formula units per unit cell
        """
        element = self.driver.find_element_by_id('textfieldPub3')
        return int(element.get_attribute('value').strip())

    def get_pearson(self):
        """
        Use By.ID to locate 'Pearson Symbol' ['textfieldPub6'], parse its
        'value' attribute.

        Return: (string) Pearson symbol if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldPub6')
        return element.get_attribute('value').strip()

    def get_crystal_class(self):
        """
        Use By.ID to locate 'Crystal Class' ['textfieldPub9'], parse its 'value'
        attribute.

        Return: (string) Crystal class if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldPub9')
        return element.get_attribute('value').strip()

    def get_structural_prototype(self):
        """
        Use By.ID to locate 'Structure Type' ['textfieldPub12'], parse its
        'value' attribute.

        Return: (string) Structure type if available, empty string otherwise
        """
        element = self.driver.find_element_by_id('textfieldPub12')
        return element.get_attribute('value').strip()

    # panel: "Bibliography"
    def _get_references(self, n):
        """
        Use By.XPATH to locate 'td' nodes with the tag name (stored in
        `tags.ICSD_PARSE_TAGS`), parse the text for each node.
        ['Detailed View' page has text fields for 3 references]

        Arguments:
            n: which-th reference to parse (= 0/1/2)

        Return: (string) Reference if available, empty string otherwise
        """
        tag = 'Reference'
        xpath = "//td[text()[contains(., '{}')]]/../td/div".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        reference = self._clean_reference_string(nodes[n].text)
        return reference

    def get_reference_1(self):
        """
        Parse '1st Reference' on the 'Detailed View' page.

        Return: (string) Reference if available, empty string otherwise
        """
        return self._get_references(0)

    def get_reference_2(self):
        """
        Parse '2nd Reference' on the 'Detailed View' page.

        Return: (string) Reference if available, empty string otherwise
        """
        return self._get_references(1)

    def get_reference_3(self):
        """
        Parse '3rd Reference' on the 'Detailed View' page.

        Return: (string) Reference if available, empty string otherwise
        """
        return self._get_references(2)

    def _clean_reference_string(self, r):
        """
        Strip the reference string of unrelated text.

        Arguments:
            r: Reference string to be cleaned

        Return: (string) r, stripped
        """
        r = r.strip()
        r = r.replace('Northwestern University Library', '').strip()
        r = r.replace('\n', ' ')
        return r

    # panel: "Warnings & Comments"
    def get_warnings(self):
        """
        Use By.ID to locate 'Warnings & Comments' ('ir_a_8_81a3e') block, then
        use By.XPATH to locate rows in the 'Warnings' table
        ('.//table/tbody/tr'), add text in each row, if any, to a list.

        Return: (list) A list of warnings if any, empty list otherwise
        """
        warnings = []
        block_element = self.driver.find_element_by_id('ir_a_8_81a3e')
        warning_nodes = block_element.find_elements_by_xpath(".//table/tbody/tr")
        for node in warning_nodes:
            if node.text:
                warnings.append(node.text.strip().replace('\n', ' '))
        return warnings

    def get_comments(self):
        """
        Use By.ID to locate 'Warnings & Comments' ('ir_a_8_81a3e') block, then
        use By.XPATH to locate the individual 'Comments' divs, add text in each
        div, if any, to a list.

        Return: (list) A list of comments if any, empty list otherwise
        """
        comments = []
        block_element = self.driver.find_element_by_id('ir_a_8_81a3e')
        tag = ICSD_PARSE_TAGS['comments']
        xpath = ".//div[text()[contains(., '{}')]]/../../div/div/div".format(tag)
        comment_nodes = block_element.find_elements_by_xpath(xpath)
        for node in comment_nodes:
            if node.text:
                comments.append(node.text.strip().replace('\n', ' '))
        return comments

    # panel: "Experimental Conditions"
    # text fields
    def get_temperature(self):
        """
        Use By.XPATH to locate the 'input' nodes associated with the div name
        (stored in `tag.ICSD_PARSE_TAGS`), and get the 'value' attribute of the
        first node.

        Return: (string) Temperature if available, empty string otherwise
        """
        temperature = ''
        tag = ICSD_PARSE_TAGS['temperature']
        xpath = "//div[text()[contains(., '{}')]]/../../td/input".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        temperature = nodes[0].get_attribute('value').strip()
        return temperature

    def get_pressure(self):
        """
        Use By.XPATH to locate the 'input' nodes associated with the div name
        (stored in `tag.ICSD_PARSE_TAGS`), and get the 'value' attribute of the
        second node.

        Return: (string) Pressure if available, empty string otherwise
        """
        pressure = ''
        tag = ICSD_PARSE_TAGS['pressure']
        xpath = "//div[text()[contains(., '{}')]]/../../td/input".format(tag)
        nodes = self.driver.find_elements_by_xpath(xpath)
        pressure = nodes[1].get_attribute('value').strip()
        return pressure

    def get_R_value(self):
        """
        Use By.XPATH to locate the 'input' node with attribute 'text',
        associated with 'td' node with the tag name (stored in
        `tags.ICSD_PARSE_TAGS`), get its 'value' attribute.

        Return: (float) R-value if available, None otherwise
        """
        R_value = None
        tag = ICSD_PARSE_TAGS['R_value']
        xpath = "//td[text()[contains(., '{}')]]".format(tag)
        xpath += "/../td/input[@type='text']"
        node = self.driver.find_element_by_xpath(xpath)
        R_value = node.get_attribute('value').strip()
        if R_value:
            R_value = float(R_value)
        return R_value

    # checkboxes
    def _is_checkbox_enabled(self, tag_key):
        """
        Use By.XPATH to locate the 'input' node of type 'checkbox' associated
        with a 'td' node with the tag name (stored in `tags.ICSD_PARSE_TAGS`),
        and try to get its 'checked' attribute.

        Return: (bool) True if checked, False otherwise
        """
        tag = ICSD_PARSE_TAGS[tag_key]
        xpath = "//*[text()[contains(., '{}')]]".format(tag)
        xpath += "/../input[@type='checkbox']"
        node = self.driver.find_element_by_xpath(xpath)
        if node.get_attribute('checked') is None:
            return False
        else:
            return True

    # subpanel: "Radiation Type"
    def is_x_ray(self):
        """
        Is the 'X-ray' checkbox enabled?
        """
        return self._is_checkbox_enabled('x_ray')

    def is_electron_diffraction(self):
        """
        Is the 'Electrons' checkbox enabled?
        """
        return self._is_checkbox_enabled('electron_diffraction')

    def is_neutron_diffraction(self):
        """
        Is the 'Neutrons' checkbox enabled?
        """
        return self._is_checkbox_enabled('neutron_diffraction')

    def is_synchrotron(self):
        """
        Is the 'Synchrotron' checkbox enabled?
        """
        return self._is_checkbox_enabled('synchrotron')

    # subpanel: "Sample Type"
    def is_powder(self):
        """
        Is the 'Powder' checkbox enabled?
        """
        return self._is_checkbox_enabled('powder')

    def is_single_crystal(self):
        """
        Is the 'Single-Cystal' checkbox enabled?
        """
        return self._is_checkbox_enabled('single_crystal')

    # subpanel: "Additional Information"
    def is_twinned_crystal_data(self):
        """
        Is the 'Twinned Crystal Data' checkbox enabled?
        """
        return self._is_checkbox_enabled('twinned_crystal_data')

    def is_rietveld_employed(self):
        """
        Is the 'Rietveld Refinement employed' checkbox enabled?
        """
        return self._is_checkbox_enabled('rietveld_employed')

    def is_absolute_config_determined(self):
        """
        Is the 'Absolute Configuration Determined' checkbox enabled?
        """
        return self._is_checkbox_enabled('absolute_config_determined')

    def is_theoretical_calculation(self):
        """
        Is the 'Theoretically calculated structures' checkbox enabled?
        """
        return self._is_checkbox_enabled('theoretical_calculation')

    def is_magnetic_structure_available(self):
        """
        Is the 'Magnetic Structure Available' checkbox enabled?
        """
        return self._is_checkbox_enabled('magnetic_structure_available')

    def is_anharmonic_temperature_factors_given(self):
        """
        Is the 'Anharmonic temperature factors given' checkbox enabled?
        """
        return self._is_checkbox_enabled('anharmonic_temperature_factors_given')

    def is_NMR_data_available(self):
        """
        Is the 'NMR Data available' checkbox enabled?
        """
        return self._is_checkbox_enabled('NMR_data_available')

    def is_correction_of_previous(self):
        """
        Is the 'Correction of Earlier Work' checkbox enabled?
        """
        return self._is_checkbox_enabled('correction_of_previous')

    # subpanel: "Properties of Structure"
    def is_polytype(self):
        """
        Is the 'Polytype Structure' checkbox enabled?
        """
        return self._is_checkbox_enabled('polytype')

    def is_order_disorder(self):
        """
        Is the 'Order/Disorder Structure' checkbox enabled?
        """
        return self._is_checkbox_enabled('order_disorder')

    def is_disordered(self):
        """
        Is the 'Disordered Structure' checkbox enabled?
        """
        return self._is_checkbox_enabled('disordered')

    def is_defect(self):
        """
        Is the 'Defect Structure' checkbox enabled?
        """
        return self._is_checkbox_enabled('defect')

    def is_misfit_layer(self):
        """
        Is the 'Misfit Layer Structure' checkbox enabled?
        """
        return self._is_checkbox_enabled('misfit_layer')

    def is_mineral(self):
        """
        Is the 'Mineral' checkbox enabled?
        """
        return self._is_checkbox_enabled('mineral')

    def is_is_prototype_structure(self):
        """
        Is the 'Structure Prototype' checkbox enabled?
        """
        return self._is_checkbox_enabled('is_prototype_structure')

    def export_CIF(self, base_filename='ICSD_Coll_Code'):
        """
        Use By.ID to locate text field for base filename for CIFs
        ('fileNameForExportToCif'), POST `base_filename` to it, and then use
        By.ID to locate 'Export to CIF File' button ('aExportCifFile'), and
        click it.

        Keyword arguments:
            base_filename: (default: 'ICSD_Coll_Code')
                           String to be prepended to the CIF file. The final
                           name is of the form
                           "[base_filename]_[ICSD Collection Code].cif", e.g.,
                           "ICSD_Coll_Code_18975.cif"
        """
        filename_element = self.driver.find_element_by_id('fileNameForExportToCif')
        filename_element.clear()
        filename_element.send_keys(base_filename)
        self.driver.find_element_by_id('aExportCifFile').click()

    def save_screenshot(self, size=(1600,900), fname='ICSD.png'):
        """
        Save screenshot of the current page.

        Keyword arguments:
            size: (default: (1600,900))
                tuple (width, height) of the current window

            fname: (default: 'ICSD.png')
                save screenshot into this file
        """
        self.driver.set_window_size(size[0], size[1])
        self.driver.save_screenshot(fname)

    def quit(self):
        self.driver.stop_client()
        self.driver.quit()

    def perform_icsd_query(self):
        """
        Post the query to form, parse data for all the entries. (wrapper)
        """
        self.post_query_to_form()
        self._click_select_all()
        self._click_show_detailed_view()
        self.parse_entries()
