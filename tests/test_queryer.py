from queryer import icsdqueryer

url = 'https://icsd.fiz-karlsruhe.de/search/basic.xhtml'
query = {
    'composition': 'TME F',
    'number_of_elements': '2'
    }
##query = {'icsd_collection_code': 105420}
queryer = icsdqueryer.Queryer(query=query)
queryer.post_query_to_form()
print queryer.hits
queryer.quit()
##queryer._click_select_all()
##queryer._click_show_detailed_view()
##queryer.export_CIF()
##queryer.parse_entries()

