# coding utf-8
# ᛝ

from datetime import datetime
import logging
from urllib.parse import urlparse, parse_qs

import requests

import common.constants as constants
from domain import ReceiptIdentity

class OFDFetcher:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def parse_url(self, url, isRemote=True) -> ReceiptIdentity:
        if not isRemote:
            fn, rn, fd, fs = map(str, url.split('_'))
            return ReceiptIdentity(
                url = url,
                fiscal_number = fn,
                fiscal_sign = fs,
                fiscal_datetime = datetime.strptime(fd, "%Y%m%d%H%M%S"),
                register_number = rn
            )
        
        parsed = urlparse(url)
        query_sequense = parse_qs(parsed.query)

        return ReceiptIdentity(
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
        response = requests.get(url, timeout=constants.REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text

    def get_receipt(self, url: str, isRemote=True):
        return self.__get_remote_receipt(url) if isRemote else self.__get_local_receipt(url)
