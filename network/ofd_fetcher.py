# coding utf-8
# ᛝ

from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests

from domain import ReceiptIdentity
from logger.logger import setup_logger
#from tests.utils import write_json


class OFDFetcher:
    def __init__(self):
        self.__logger = setup_logger(
            name='ofd_fetcher'
            logfile='ofd_fetcher.log'
        )
    
    def parse_url(self, url) -> ReceiptIdentity:        
        parsed = urlparse(url)
        query_sequense = parse_qs(parsed.query)
        
        url_args = ReceiptIdentity(
            url = url,
            fiscal_number = query_sequense["t"][0],
            fiscal_sign = query_sequense['s'][0],
            fiscal_datetime = datetime.strptime(query_sequense['c'][0], "%Y%m%d%H%M%S"),
            register_number = query_sequense['r'][0]
        )
        
        self.__logger.info(
            "parse utl:%s %s", url, url_args
        )

        return url_args
    
    def get_receipt(self, url: str):
        response = requests.get(url)
        
        self.__logger.info("fetch receipt by url:%s", url)
        self.__logger.info("response status code: %d", response.status_code)
        
        #url_args = self.parse_url(url)
        #write_json(response.text, url_args)
        
        return response.text
