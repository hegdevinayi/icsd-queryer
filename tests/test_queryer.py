import queryer

query = {
    'composition': 'Ni:1:1',
    'number_of_elements': '1'
    }
q = queryer.Queryer(use_login=True,
                    query=query,
                    structure_sources=['e', 't'])
q.perform_icsd_query()
