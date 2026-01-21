#! /usr/bin/env python3

# coding utf-8
import json
import sys
from traceback import print_exc

import requests
from bs4 import BeautifulSoup


def get_remote_receipt(url: str):
    response = requests.get(url)
    # debug print
    print("Status code:", response.status_code)
    with open('resource/in/test_url.html', mode='w', encoding='utf-8') as f:
        f.write(response.text)
    
    return response.text

# test
def get_local_receipt(filename: str):
    with open('resource/in/{}'.format(filename), mode='r', encoding='utf-8') as ticket_f:
        receipt_html = ticket_f.read()
    return receipt_html

def get_receipt(url: str, isRemote=True):
    return get_remote_receipt(url) if isRemote else get_local_receipt(url)

def parse_ticket(response):
    receipt_html = BeautifulSoup(response, 'html.parser')
    
    # naive parse
    ticket = receipt_html.find('div', class_='tickets')
    #for row in ticket.find('table').find_all('tr', recursive=False):
        # debug
    #    print(row)

    # Seller
    seller_name_tag = ticket.find('h3', style=lambda value: value and 'font-weight' in value)
    if not seller_name_tag:
        raise ValueError("seller name not found")

    seller_tag = seller_name_tag.parent
    seller_name = seller_name_tag.text.strip()
    texts = [
        t.strip()
        for t in seller_tag.stripped_strings
        if not t.startswith('"') and not t.isdigit()
    ]
    seller_address = texts[0] if len(texts) > 0 else None
    stir_tag = seller_tag.find("i")
    seller_stir = stir_tag.text.strip() if stir_tag else None

    # debug
    #print('seller_name: {}, seller_stir: {}\nseller_address: {}'.format(seller_name,
    #    seller_stir, seller_address))
    #print(texts)

    # Fiscal number
    fiscal_number = seller_tag.find_next('b').text.strip()

    # Date
    date_tag = ticket.find('i', string=lambda value: value and ',' in value)
    receipt_datetime = date_tag.text.strip() if date_tag else None

    # debug
    print('fiscal_number: {}'.format(fiscal_number))
    #print('date: {}'.format(receipt_datetime))

    # Products
    products = []
    products_tag = ticket.select_one('table.products-tables')
    if not products_tag:
        raise ValueError('products table not found')
    
    current = None
    products_tag_body = products_tag.find('tbody')
    # degub 
    #print("products")
    for row in products_tag_body.find_all('tr', recursive=False):
        classes = row.get('class', [])
        if 'products-row' in classes:
            cols = row.find_all('td')
            current = {
                'name': cols[0].text.strip(),
                'quantity': cols[1].text.strip(),
                'price': cols[2].text.strip(),
                'vat_amount': None,
                'vat_rate': None,
                'barcode': None,
                'mxik': None,
                'mxik_name': None,
                'unit': None,
                'discount': None
            }
            products.append(current)
        elif current and 'nds-row' in classes:
            label = row.find('td').text.lower()
            value = row.find_all('td')[-1].text.strip()

            if 'qiymati' in label:
                current['vat_amount'] = value
            elif 'foizi' in label:
                current['vat_rate'] = value
        
        elif current and 'code-row' in classes:
            label = row.find('td').text.lower()
            value = row.find_all('td')[-1].text.strip()
            # debug
            #print(label)
            if 'shtrix' in label:
                current['barcode'] = value
            elif 'mxik kodi' in label:
                current['mxik'] = value
            elif 'mxik nomi' in label:
                current['mxik_name'] = value
            elif "o'lchov" in label:
                current['unit'] = value
            elif 'chegirma' in label:
                current['discount'] = value

    # payments
    payments = {}
    #debug
    #print('payments:\n')
    for row in ticket.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) == 2:
            key = cols[0].text.strip()
            value = cols[1].text.strip()
            # debug
            #print(key)
            if key in ('Naqd pul', 'Bank kartalari'):
                payments[key] = value
            
            if key == 'Bank kartasi turi':
                payments['card_type'] = value

    # totals
    total_sum = None
    total_vat = None
    #debug
    #print('totals:\n')
    for row in ticket.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) == 2:
            label = cols[0].text.lower()
            value = cols[1].text.strip()
            # debug
            #print(label)
            if 'jami' in label:
                total_sum = value
            elif 'qqs' in label:
                total_vat = value

    # result
    return {
        "receipt": {
            "fiscal_number": fiscal_number,
            "datetime": receipt_datetime,
            "seller": {
                "name": seller_name,
                "stir": seller_stir,
            },
            "total_sum": total_sum,
            "total_vat": total_vat,
            "payments": payments,
        },
        "products": products,
    }

def write_receipt_as_json(receipt):
    # debug
    #print(receipt['receipt']['fiscal_number'])
    with open('resource/out/{}.json'.format(receipt['receipt']['fiscal_number']), mode='w', encoding='utf-8') as f:
        f.write(json.dumps(receipt, ensure_ascii=False, indent=4))

if __name__ == '__main__':
    try:
        #test_url = "https://ofd.soliq.uz/check?t=LG420230638021&r=5240&c=20260109143119&s=430522013780"
        test_filename = './test_url.html'
        test_url = 'https://ofd.soliq.uz/check?t=UZ210317270659&r=38938&c=20260110145519&s=299114273494'
        receipt = get_receipt(test_url)
        #receipt = get_receipt(test_filename, False)
        parsed_ticket = parse_ticket(receipt)

        #debug
        #print(parsed_ticket)
        write_receipt_as_json(parsed_ticket)
    except Exception as e:
        print('Error:{}'.format(e))
        print_exc()
        sys.exit(-1)