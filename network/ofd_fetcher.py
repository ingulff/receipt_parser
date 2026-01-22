# coding utf-8
# ᛝ

from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests

from domain import ReceiptUrl

class OFDFetcher:
    def parse_url(self, url, isRemote=True) -> ReceiptUrl:
        if not isRemote:
            fn, rn, fd, fs = map(str, url.split('_'))
            return ReceiptUrl(
                url = url,
                fiscal_number = fn,
                fiscal_sign = fs,
                fiscal_datetime = datetime.strptime(fd, "%Y%m%d%H%M%S"),
                register_number = rn
            )
        
        parsed = urlparse(url)
        query_sequense = parse_qs(parsed.query)

        return ReceiptUrl(
            url = url,
            fiscal_number = query_sequense["t"][0],
            fiscal_sign = query_sequense['s'][0],
            fiscal_datetime = datetime.strptime(query_sequense['c'][0], "%Y%m%d%H%M%S"),
            register_number = query_sequense['r'][0]
        )

    # test
    def __get_local_receipt(self, filename: str):
        with open('resource/in/{}'.format(filename), mode='r', encoding='utf-8') as ticket_f:
            receipt_html = ticket_f.read()
        return receipt_html

    def __get_remote_receipt(self, url: str):
        response = requests.get(url)
        # debug print
        print("Status code:", response.status_code)
        url_args = self.parse_url(url)
        with open('resource/in/{}.html'.format(url_args['fiscal_number']), mode='w', encoding='utf-8') as f:
            f.write(response.text)
        
        return response.text

    def get_receipt(self, url: str, isRemote=True):
        return self.__get_remote_receipt(url) if isRemote else self.__get_local_receipt(url)
