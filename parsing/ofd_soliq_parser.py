# coding utf-8
# ᛝ

from datetime import datetime
from decimal import Decimal
from typing import List

from bs4 import BeautifulSoup

from domain import CashRegister, Payment, Product, ReceiptMeta, ReceiptUrl, Receipt, Store


class OFDSoliqParser:
    def __parse_receipt_meta(self, meta_tag, rows, receipt_meta: ReceiptUrl) -> ReceiptMeta:
        fiscal_number = meta_tag.find_next('b').text.strip()
        if receipt_meta.fiscal_number != fiscal_number:
            raise ValueError("invalid fiscal number")
        
        register_number = meta_tag.find_next('span').find_next('b').text.strip()
        if receipt_meta.register_number != register_number: 
            raise ValueError("invalid register number")

        total_sum = None
        total_vat = None
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                label = cols[0].text.lower()
                value = (
                    cols[1].text
                        .replace('\xa0', '')
                        .replace(' ', '')
                        .replace(',', '')
                        .replace('%', '')
                        .strip()
                )
                if 'jami' in label:
                    total_sum = Decimal(value)
                elif 'qqs' in label:
                    total_vat = Decimal(value)

        return ReceiptMeta(
            fiscal_number = fiscal_number,
            fiscal_sign = receipt_meta.fiscal_sign,
            fiscal_datetime = receipt_meta.fiscal_datetime,
            register_number = register_number,
            total_amount = total_sum,
            total_vat = total_vat
        )


    def __parse_store(self, store_tag) -> Store:
        seller_name_tag = store_tag.find('h3', style=lambda value: value and 'font-weight' in value)
        if not seller_name_tag:
            raise ValueError("seller name not found")

        seller_tag = seller_name_tag.parent
        store_labels = [
            t.strip()
            for t in seller_tag.stripped_strings
            if not t.startswith('"') and not t.isdigit()
        ]
        
        seller_tin_tag = seller_tag.find("i")
        if not seller_tin_tag:
            raise ValueError("seller tin not found")
        
        return Store(
            seller_tin = seller_tin_tag.text.strip(),
            seller_name = seller_name_tag.text.strip(),
            address = store_labels[0]
        )

    def __parse_cach_register(self, cash_register_tag) -> CashRegister:
        serial_number = None
        name = None
        for row in cash_register_tag.find_all('span'):
            if 'sn' in row.text.lower().strip():
                serial_number = row.find_next('b').text.strip()
            
            if 'nkm nomi' in row.text.lower().strip():
                name = row.find_next('b').text.strip()
        
        return CashRegister(
            serial_number = serial_number,
            name = name
        )

    def __parse_payment(self, datetime_tag, rows) -> Payment:
        payment_dt = datetime.strptime(datetime_tag.text.strip(), "%d.%m.%Y, %H:%M")
        cash_amount = None
        card_amount = None
        card_type = None

        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                key = cols[0].text.strip()
                value = cols[1].text.strip()
                if key in ('Naqd pul'):
                    cash_amount = Decimal(
                        value
                        .replace('\xa0', '')
                        .replace(' ', '')
                        .replace(',', '')
                        .replace('%', '')
                    )
                
                if key in ('Bank kartalari'):
                    card_amount = Decimal(
                        value
                        .replace('\xa0', '')
                        .replace(' ', '')
                        .replace(',', '')
                        .replace('%', '')
                    )
                
                if key == 'Bank kartasi turi':
                    card_type = value
        
        return Payment(
            cash_amount = cash_amount,
            card_amount = card_amount,
            card_type = card_type,
            datetime = payment_dt
        )

    def __parse_products(self, products_tag) -> List[Product]:
        if not products_tag:
            raise ValueError('products table not found')
        
        products_tag_body = products_tag.find('tbody')
        products = []
        current_product = None
        for row in products_tag_body.find_all('tr', recursive=False):
            classes = row.get('class', [])
            if 'products-row' in classes:
                cols = row.find_all('td')
                current_product = {
                    'name': cols[0].text.strip(),
                    'quantity': cols[1].text.strip(),
                    'price': (
                        cols[2].text.strip()
                        .replace('\xa0', '')
                        .replace(' ', '')
                        .replace(',', '')
                        .replace('%', '')
                    ),
                    'vat_amount': None,
                    'vat_rate': None,
                    'barcode': None,
                    'pic': None,
                    'pic_name': None,
                    'unit': None,
                    'discount': None
                }
                
            elif current_product and 'nds-row' in classes:
                label = row.find('td').text.lower()
                value = row.find_all('td')[-1].text.strip()

                if 'qiymati' in label:
                    current_product['vat_amount'] = (
                        value
                        .replace('\xa0', '')
                        .replace(' ', '')
                        .replace(',', '')
                        .replace('%', '')
                    )
                elif 'foizi' in label:
                    current_product['vat_rate'] = (
                        value
                        .replace('\xa0', '')
                        .replace(' ', '')
                        .replace(',', '')
                        .replace('%', '')
                    )
            
            elif current_product and 'code-row' in classes:
                label = row.find('td').text.lower()
                value = row.find_all('td')[-1].text.strip()
                if 'shtrix' in label:
                    current_product['barcode'] = value
                elif 'mxik kodi' in label:
                    current_product['pic'] = value
                elif 'mxik nomi' in label:
                    current_product['pic_name'] = value
                elif "o'lchov" in label:
                    current_product['unit'] = value
                elif 'chegirma' in label:
                    current_product['discount'] = value
                elif 'komitent' in label:
                    products.append(Product(
                        pic = current_product['pic'],
                        pic_name = current_product['pic_name'],
                        barcode = current_product['barcode'],
                        price = current_product['price'],
                        quantity = current_product['quantity'],
                        vat_amount = current_product['vat_amount'],
                        vat_rate = current_product['vat_rate'],
                        name = current_product['name'],
                        unit = current_product['unit'],
                        discount = current_product['discount']
                    ))
        
        return products
        

    def parse(self, raw_receipt, receipt_meta: ReceiptUrl) -> Receipt:
        receipt_html = BeautifulSoup(raw_receipt, 'html.parser')

        ticket = receipt_html.find('div', class_='tickets')
        all_rows = ticket.find_all('tr')
        
        receipt_meta = self.__parse_receipt_meta(ticket, all_rows, receipt_meta)
        store = self.__parse_store(ticket)

        cash_register = self.__parse_cach_register(ticket)

        date_tag = ticket.find('i', string=lambda value: value and ',' in value)
        payment = self.__parse_payment(date_tag, all_rows)
    
        products_tag = ticket.select_one('table.products-tables')
        products = self.__parse_products(products_tag)

        # result
        return Receipt(
            receipt_meta = receipt_meta,
            store = store,
            cash_register = cash_register,
            payment = payment,
            products = products
        )
    

