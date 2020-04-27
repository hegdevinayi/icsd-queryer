import logging
import queryer


logging.root.setLevel(logging.DEBUG)


query = {
    'composition': 'Al:1:1',
    'number_of_elements': '1'
    }
q = queryer.Queryer(use_login=True,
                    query=query,
                    structure_sources=['e', 't'])
q.perform_icsd_query()
