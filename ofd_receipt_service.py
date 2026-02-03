#! /usr/bin/env python3

# coding utf-8
# ᛝ

import json
from dataclasses import asdict
import sys
from traceback import print_exc

from database import DatabaseSession, Transaction, ReceiptStatus
from logger.logger import setup_logger
from network import OFDFetcher
from parsing import OFDSoliqParser



class OFDFetchServise:
    def __init__(self, fetcher, parser):
        self.__fetcher = fetcher
        self.__parser = parser
        self.__database = DatabaseSession('./resource/db/receipts.db')
        self.__logger = setup_logger(
            name='ofd_servise',
            logfile='ofd_service.log'
        )

    def __process_url(self, url, isRemote=False):
        self.__logger.info("start parsing receipt:%s", url)
        receipt_url = self.__fetcher.parse_url(url, isRemote)
        exist_receipt = False
        with Transaction(self.__database) as t:
            exist_receipt = t.receipt_identity.exist(
                receipt_url.fiscal_number, 
                receipt_url.fiscal_sign
            ):
                self.__logger.warning("receipt always exist: %s", url)
            else:
                t.receipt_identity.create(receipt_url)

        raw_receipt = self.__fetcher.get_receipt(url, isRemote)
        with Transaction(self.__database) as t:
            t.receipt_identity.update_status(
                receipt_url.fiscal_number, 
                receipt_url.fiscal_sign, 
                ReceiptStatus.FETCHED)
        
        receipt = self.__parser.parse(raw_receipt, receipt_url)
        with Transaction(self.__database) as t:
            status = t.receipt_identity.status(receipt_url.fiscal_number, receipt_url.fiscal_sign)
            if status and status < ReceiptStatus.PARSED:
                t.seller.create(receipt.store, receipt.cash_register)
                seller_store_ids = {
                    "receipt_identity_id": t.receipt_identity.id(
                        receipt_url.fiscal_number, receipt_url.fiscal_sign),
                    "seller_id": t.seller.seller_id(receipt.store.seller_tin),
                    "cash_register_id": t.seller.cash_register_id(receipt.cash_register.serial_number)
                }
                t.receipt.create(receipt, seller_store_ids)
                t.receipt_identity.update_status(
                    receipt_url.fiscal_number, 
                    receipt_url.fiscal_sign, 
                    ReceiptStatus.PARSED)

        self.__logger.info("Cmplete parsing receipt:%s", url)
        self.write_receipt_as_json(receipt)

    def __process_urls(self, isRemote=False):
        urls = self.__local_urls
        if isRemote:
            urls = self.__remote_urls
        
        for url in urls:
            self.__process_url(url, isRemote)

    def run(self, url_setting):
        self.__database.open()
        self.__process_urls(url_setting['isRemote'])
        self.__database.close()

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
        
        ofd_fetch_service = OFDFetchServise(OFDFetcher(), OFDSoliqParser(), local_urls)
        ofd_fetch_service.run(local_urls)
    except Exception as e:
        print('Error:{}'.format(e))
        print_exc()
        sys.exit(-1)