import queryer

query = {
    'composition': 'Ni:1:1 Ti:2:2',
    'number_of_elements': '2'
    }
##query = {'icsd_collection_code': 181801}
queryer = queryer.Queryer(query=query)
queryer.perform_icsd_query()
##print queryer.hits
##queryer.quit()

