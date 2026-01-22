#! /usr/bin/env python3

# coding utf-8
# ᛝ

import json
from dataclasses import asdict
import sys
from traceback import print_exc

from network import OFDFetcher
from parsing import OFDSoliqParser

class OFDFetchServise:
    def __init__(self, local_urls, remote_urls):
        # todo delete it
        self.__local_urls = local_urls
        self.__remote_urls = remote_urls
        self.__raw_receipts = []
        
        self.__fetcher = OFDFetcher()
        self.__parser = OFDSoliqParser()

    def __process_url(self, url, isRemote=False):
        raw_receipt = self.__fetcher.get_receipt(url, isRemote)
        receipt_url = self.__fetcher.parse_url(url, isRemote)
        receipt = self.__parser.parse(raw_receipt, receipt_url)
        
        self.write_receipt_as_json(receipt)

    def __process_urls(self, isRemote=False):
        urls = self.__local_urls
        if isRemote:
            urls = self.__remote_urls
        
        for url in urls:
            self.__process_url(url, isRemote)

    def run(self, isRemote=False):
        self.__process_urls(isRemote)

    def write_receipt_as_json(self, receipt):
        with open('resource/out/expected_{}.json'.format(receipt.receipt_meta.fiscal_number), mode='w', encoding='utf-8') as f:
            f.write(json.dumps(asdict(receipt), ensure_ascii=False, indent=4, default=str))


if __name__ == '__main__':
    try:
        remote_urls = [
            'https://ofd.soliq.uz/check?t=LG420230638021&r=5240&c=20260109143119&s=430522013780',
            'https://ofd.soliq.uz/check?t=UZ210317270659&r=38938&c=20260110145519&s=299114273494'
        ]
        local_urls = [
            'UZ210317270659_38938_20260110145519_299114273494.html',
            'LG420230638021_5240_20260109143119_430522013780.html'
        ]
        
        ofd_fetch_service = OFDFetchServise(local_urls, remote_urls)
        ofd_fetch_service.run(isRemote=False)
    except Exception as e:
        print('Error:{}'.format(e))
        print_exc()
        sys.exit(-1)