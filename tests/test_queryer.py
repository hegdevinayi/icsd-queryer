from queryer import icsdqueryer

url = 'https://icsd.fiz-karlsruhe.de/search/basic.xhtml'
query = {
    'composition': 'Ni:1:1 Ti:2:2',
    'number_of_elements': '2'
    }
query = {'icsd_collection_code': 105420}
queryer = icsdqueryer.Queryer(query=query)
queryer.post_query_to_form()
queryer._click_select_all()
queryer._click_detailed_view()
queryer.parse_data()
queryer.save_screenshot()
queryer.quit()

