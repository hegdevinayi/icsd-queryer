import queryer

url = 'https://icsd.fiz-karlsruhe.de/search/basic.xhtml'
query = {
    'composition': 'TME:8:8 NG:3:3',
    'number_of_elements': '2'
    }
##query = {'icsd_collection_code': 181801}
queryer = queryer.Queryer(query=query)
queryer.perform_icsd_query()
##print queryer.hits
##queryer.quit()

