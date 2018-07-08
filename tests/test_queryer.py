import queryer

query = {
    'composition': 'Al O F',
    'number_of_elements': '3'
    }
##query = {'icsd_collection_code': 181801}
queryer = queryer.Queryer(query=query, structure_source='theory')
queryer.perform_icsd_query()
