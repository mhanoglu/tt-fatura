# -*- coding: utf-8 -*-

import json
import scrapy


class TurkTelekomFaturaSpider(scrapy.Spider):
    name = 'turk-telekom'
    start_urls = ['https://onlineislemler.turktelekom.com.tr/']
    login_url = 'https://onlineislemler.turktelekom.com.tr/oim/sso/login/msisdn'
    gen_session_url = 'https://onlineislemler.turktelekom.com.tr/mps/Portal?cmd=tekilOim'
    billinfo_url = 'https://onlineislemler.turktelekom.com.tr/mps/portal?cmd=billinfo'

    tokens = {}
    args = {}

    def parse(self, response):
        self.log("parsed response")
        return self.request_login()

    def request_login(self):
        self.args['phone_number'] = getattr(self, 'phone', None)
        self.args['sms_code'] = getattr(self, 'code', None)

        self.log("request_login with %s and %s" % (self.args['phone_number'], self.args['sms_code']))

        return scrapy.http.FormRequest(
            self.login_url,
            body=json.dumps({"msisdn": self.args['phone_number'], "otp": self.args['sms_code'], "kmli": True}),
            method="POST",
            meta={'dont_redirect': True, "handle_httpstatus_list": [302]},
            callback=self.callback_login,
            headers={'Content-Type': 'application/json', 'Accept': '*/*'}
        )

    def callback_login(self, response):
        self.tokens = json.loads(response.body)['payload']['tokenDetails']

        form_data = {
            "assetId": "90" + self.args['phone_number'],
            "fromLegacy": "true",
            "accessToken": self.tokens['accessToken'],
            "refreshToken": self.tokens['refreshToken'],
            "pageCmd": "",
            "corpUni": "",
        }

        return scrapy.http.FormRequest(
            self.gen_session_url,
            formdata=form_data,
            method="POST",
            callback=self.request_billinfo,
            headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': self.gen_session_url}
        )

    def request_billinfo(self, response):
        self.log("request_billinfo started")

        return scrapy.Request(self.billinfo_url,
                              meta={'dont_redirect': True, "handle_httpstatus_list": [302]},
                              callback=self.callback_billinfo)

    def callback_billinfo(self, response):
        self.log("callback_billinfo started")

        table = []
        head = []
        for column in response.xpath('//table[@id="faturaTablosu"]/tr[@class="table-header"]/th/b/text()'):
            head.append(column.get())

        del head[-2]  # Remove "Fatura Detayları" column from head
        table.append(head)

        for row in response.xpath('//table[@id="faturaTablosu"]/tr[not(@class="table-header")]'):
            sel = scrapy.selector.Selector(text=row.get())

            columns = []
            paid_status = 'Ödenmedi'.decode('u8')
            amount = None
            for col in sel.xpath('//td'):
                columns.append(col.css('::text').get())

                if not amount:
                    amount = col.xpath('//input[@data-amount]').attrib['data-amount']

                if col.xpath('//strong/p/span').attrib['class'] == 'bill-image-paid':
                    paid_status = 'Ödendi'.decode('u8')

            # Remove last two columns
            columns = columns[:-2]

            # Add amount to first index
            columns[0] = amount

            # Add paid status to columns
            columns.append(paid_status)

            table.append(columns)

        max_width = max([max([len(col.encode('u8')) for col in cols]) for cols in table])
        for row in table:
            for col in row:
                print col.rjust(max_width),
            print
