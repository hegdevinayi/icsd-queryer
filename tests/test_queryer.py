from queryer import icsdqueryer


url = 'https://icsd.fiz-karlsruhe.de/search/basic.xhtml'
query = {
        1:('content_form:uiChemistrySearchSumForm:input', 'Ni:1:1 Ti:1:1'),
        2:('content_form:uiChemistrySearchElCount:input:input', '2')
        }
queryer = icsdqueryer.Queryer(query=query)
queryer.post_query_to_form()
queryer._click_select_all()
queryer._click_detailed_view()
queryer.parse_data()
## queryer.save_screenshot()

##rietveld = self.driver.find_elements_by_xpath("//*[contains(text(), 'Rietveld')]")
##print rietveld[0].find_element_by_xpath('//input').is_enabled()
##theory = self.driver.find_elements_by_xpath("//*[contains(text(), 'Theoretically')]")
##print theory[0].find_element_by_xpath('//input').is_enabled()


