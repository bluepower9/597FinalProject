import json
from util.util import read_configs

__base_path = './util/openai/'
APIKEY = read_configs(__base_path + 'keys.json')['api_key']