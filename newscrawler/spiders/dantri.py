# -*- coding: utf-8 -*-
import scrapy
import os
import re
from datetime import datetime, timedelta, date
import json

class DantriSpider(scrapy.Spider):
    name = 'dantri'
    allowed_domains = ['dantri.com.vn']
    date_format = '%d-%m-%Y'
    folder = 'data/dantri'
    # start_urls = ['http://dantri.com.vn/xa-hoi/ddkhoi-lua-bao-trum-can-nha-chua-hang-chuc-binh-gas-0171117204139233.htm']

    base_urls = ['http://dantri.com.vn/su-kien/{}.htm',
            'http://dantri.com.vn/xa-hoi{}.htm',
            'http://dantri.com.vn/the-gioi/{}.htm',
            'http://dantri.com.vn/the-thao/{}.htm',
            'http://dantri.com.vn/giao-duc-khuyen-hoc/{}.htm',
            'http://dantri.com.vn/tam-long-nhan-ai/{}.htm',
            'http://dantri.com.vn/kinh-doanh/{}.htm',
            'http://dantri.com.vn/van-hoa/{}.htm',
            'http://dantri.com.vn/giai-tri/{}.htm',
            'http://dantri.com.vn/phap-luat/{}.htm',
            'http://dantri.com.vn/nhip-song-tre/{}.htm',
            'http://dantri.com.vn/suc-khoe/{}.htm',
            'http://dantri.com.vn/suc-manh-so/{}.htm',
            'http://dantri.com.vn/o-to-xe-may/{}.htm',
            'http://dantri.com.vn/tinh-yeu-gioi-tinh/{}.htm',
            'http://dantri.com.vn/chuyen-la/{}.htm']

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super(DantriSpider, self).__init__(*args, **kwargs)
        date_now = datetime.now().date()

        if from_date is not None:
            # if has from_date option then check to_date option
            self.from_date = datetime.strptime(from_date, self.date_format).date()
            if to_date is not None:
                self.to_date = datetime.strptime(to_date, self.date_format).date()
                if self.to_date > date_now:
                    raise ValueError('to_date must be less than or equal to {}'.format(date_now.strftime(self.date_format)))
            else:
                self.to_date = date_now
        else:
            self.from_date = date_now
            self.to_date = date_now

        if self.from_date > self.to_date:
            raise ValueError('from_date must be less than or equal to to_date')

        if not os.path.exists(self.folder):
            os.makedirs(self.folder)


    def start_requests(self):
        delta = timedelta(days=1)
        d = self.from_date
        while d <= self.to_date:
            date = d.strftime(self.date_format)
            for base_url in self.base_urls:
                url = base_url.format(date)
                yield scrapy.Request(url=url, callback=self.parse_checklist_page)

            d += delta
                

    def parse_checklist_page(self, response):
        urls = response.css('div#listcheckepl>div>a::attr(href)').extract()
        for url in urls:
            yield response.follow(url=url, callback=self.parse_news)


    def parse_news(self, response):
        content_div = response.css('div#ctl00_IDContent_ctl00_divContent')
        time = response.css('span.tt-capitalize::text').extract_first()
        time = self.normalizeTime(time)
        title = content_div.css('h1::text').extract_first()
        title = self.remove_scpecial_characters(title)
        description = content_div.css('h1::text').extract_first()
        description = self.remove_scpecial_characters(description)
        paragraphs = content_div.css('div#divNewsContent p:not([style])::text').extract()
        content = ' '.join(map(self.remove_scpecial_characters, paragraphs))

        self.write_to_file({'url': response.url, 'title': title, 'description': description, 
                            'time': time, 'content': content})


    def remove_scpecial_characters(self, str):
        return re.sub(r'[“”?!\n\r:;",.\t]+|<.*?>', ' ', str)


    def normalizeTime(self, raw_time_str):
        time_str = re.sub(r'[^/0-9:-]', '', raw_time_str)
        datetime_obj = datetime.strptime(time_str, '%d/%m/%Y-%H:%M')
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')


    def exists_file_name(self, url, time):
        title = re.sub(r'[^0-9]', '', url)
        time = re.sub(r'[^0-9]', '_', time)
        folder = self.folder + '/' + time[:10]
        file_name = 'data/dantri/{}/{}__{}.json'.format(folder, title, time)
        return os.path.exists(file_name)


    def write_to_file(self, data):
        title = re.sub(r'[^0-9]', '', data['url'])
        time = re.sub(r'[^0-9]', '_', data['time'])
        folder = self.folder + '/' + time[:10]
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = '{}/{}__{}.json'.format(folder, title, time)
        with open(file_name, 'w', encoding="utf-8") as outfile:
            json.dump(data, outfile, ensure_ascii=False)