# -*- coding: utf-8 -*-
import scrapy
import re
import json
import os
from datetime import datetime, timedelta, date
from .CustomSpider import CustomSpider

class A24hSpider(CustomSpider):
    name = '24h'
    allowed_domains = ['24h.com.vn']
    base_url = 'http://www.24h.com.vn/ajax/box_bai_viet_cung_chuyen_muc/index/{}/0/{}/9/1/12/0?page={}'
    categories = [
        {'id': '46', 'url': '/tin-tuc-trong-ngay-c46.html'},
        {'id': '48', 'url': '/bong-da-c48.html'},
        {'id': '415', 'url': '/tin-tuc-quoc-te-c415.html'},
        {'id': '78', 'url': '/thoi-trang-c78.html'},
        {'id': '51', 'url': '/an-ninh-hinh-su-c51.html'},
        {'id': '407', 'url': '/thoi-trang-hi-tech-c407.html'},
        {'id': '161', 'url': '/tai-chinh-bat-dong-san-c161.html'},
        {'id': '460', 'url': '/am-thuc-c460.html'},
        {'id': '145', 'url': '/lam-dep-c145.html'},
        {'id': '729', 'url': '/doi-song-showbiz-c729.html'},
        {'id': '731', 'url': '/giai-tri-c731.html'},
        {'id': '64', 'url': '/ban-tre-cuoc-hocsong-c64.html'},
        {'id': '216', 'url': '/giao-duc-du--c216.html'},
        {'id': '101', 'url': '/the-thao-c101.html'},
        {'id': '159', 'url': '/phi-thuong-ky-quac-c159.html'},
        {'id': '55', 'url': '/cong-nghe-thong-tin-c55.html'},
        {'id': '747', 'url': '/o-to-c747.html'},
        {'id': '748', 'url': '/xe-may-xe-dap-c748.html'},
        {'id': '52', 'url': '/thi-truong-tieu-dung-c52.html'},
        {'id': '76', 'url': '/du-lich-24h-c76.html'},
        {'id': '62', 'url': '/suc-khoe-doi-song-c62.html'},
        {'id': '768', 'url': '/video-tong-hop-c768.html'},
        {'id': '746', 'url': '/cuoi-24h-c746.html'},
        {'id': '762', 'url': '/goc-do-hoa-c762.html'}
    ]
    folder = 'data/24h'
    date_url_format = '%Y-%m-%d'

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super(A24hSpider, self).__init__(from_date, to_date, *args, **kwargs)

        # if not os.path.exists(self.folder):
        #     os.makedirs(self.folder)

    def start_requests(self):
        delta = timedelta(days=1)
        d = self.from_date
        while d <= self.to_date:
            date = d.strftime(self.date_url_format)
            for category in self.categories:
                url = self.base_url.format(category['id'], date, 1)
                yield scrapy.Request(url=url, meta={'id': category['id'], 'date': date}, callback=self.parse)
            d += delta

    def parse(self, response):
        for request in self.parse_urls_on_ajax_page(response):
            yield request

        paginations = response.css('div.phantrang a::text').extract()
        for p in paginations:
            url = self.base_url.format(response.meta['id'], response.meta['date'], p)
            yield scrapy.Request(url=url, callback=self.parse_urls_on_ajax_page)


    def parse_urls_on_ajax_page(self, response):
        first_url = response.css('span#id_class_title_box_bd_tt_2 > a::attr(href)').extract_first()
        if first_url is not None:
            yield response.follow(url=first_url, callback=self.parse_news)

        news_urls = response.css('ul.listNews-trangtrong a::attr(href)').extract()
        for url in news_urls:
            yield response.follow(url=url, callback=self.parse_news)


    def parse_news(self, response):
        title = response.css('h1.baiviet-title::text').extract_first()
        title = self.remove_scpecial_characters(title)
        description = response.css('p.baiviet-sapo::text').extract_first()
        description = self.remove_scpecial_characters(description)
        time = response.css('div.baiviet-ngay').xpath('string(.)').extract_first()
        time = self.normalizeTime(time)
        paragraphs = response.css('div.text-conent>p::text').extract()
        content = ' '.join(map(self.remove_scpecial_characters, paragraphs))

        self.write_to_file({'url': response.url, 'title': title, 'description': description, 
                            'time': time, 'content': content})

    def remove_scpecial_characters(self, str):
        return re.sub(r'[“”?!\n\r:;",.\t]+|<.*?>', ' ', str)

    def normalizeTime(self, raw_time_str):
        time_str = re.sub(r'\(GMT\+7\)|[^0-9:/ ]', '', raw_time_str).strip()
        datetime_obj = datetime.strptime(time_str, '%d/%m/%Y %H:%M')
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

