import os.path
import yaml

TAGS_DIR = os.path.abspath(os.path.dirname(__file__))
query_tags_file = os.path.join(TAGS_DIR, 'query_tags.yml')
parse_tags_file = os.path.join(TAGS_DIR, 'parse_tags.yml')

with open(query_tags_file, 'r') as fr:
    ICSD_QUERY_TAGS = yaml.load(fr)

with open(parse_tags_file, 'r') as fr:
    ICSD_PARSE_TAGS = yaml.load(fr)
