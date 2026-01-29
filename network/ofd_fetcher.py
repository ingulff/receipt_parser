# coding utf-8
# ᛝ

from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests

from domain import ReceiptIdentity

class OFDFetcher:
    def parse_url(self, url) -> ReceiptIdentity:        
        parsed = urlparse(url)
        query_sequense = parse_qs(parsed.query)

        return ReceiptIdentity(
            url = url,
            fiscal_number = query_sequense["t"][0],
            fiscal_sign = query_sequense['s'][0],
            fiscal_datetime = datetime.strptime(query_sequense['c'][0], "%Y%m%d%H%M%S"),
            register_number = query_sequense['r'][0]
        )
    
    def get_receipt(self, url: str):
        response = requests.get(url)
        # debug print
        print("Status code:", response.status_code)
        url_args = self.parse_url(url)
        with open('resource/in/{}.html'.format(url_args['fiscal_number']), mode='w', encoding='utf-8') as f:
            f.write(response.text)
        
        return response.text
