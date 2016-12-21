from icsd_queryer import ICSDQueryer

url = 'https://icsd.fiz-karlsruhe.de/search/basic.xhtml'
query = {
        1:('content_form:uiChemistrySearchSumForm:input', 'Ni:2:2 Ti:1:1'),
        2:('content_form:uiChemistrySearchElCount:input:input', '2')
        }
queryer = ICSDQueryer()
queryer.get_url_request(url)
queryer.perform_query(query)
queryer.click_select_all()
queryer.click_detailed_view()
queryer.expand_all_dropdown()
queryer.save_screenshot()

##rietveld = self.driver.find_elements_by_xpath("//*[contains(text(), 'Rietveld')]")
##print rietveld[0].find_element_by_xpath('//input').is_enabled()
##theory = self.driver.find_elements_by_xpath("//*[contains(text(), 'Theoretically')]")
##print theory[0].find_element_by_xpath('//input').is_enabled()


