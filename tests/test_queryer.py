import queryer

query = {
    'composition': 'Yb F',
    'number_of_elements': '2'
    }
q = queryer.Queryer(query=query, structure_sources=['e', 't'])
#q = queryer.Queryer(query=query)
q.perform_icsd_query()
