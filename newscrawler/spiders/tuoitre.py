# -*- coding: utf-8 -*-
import scrapy
import re
import json
import os
from datetime import datetime, timedelta, date
from .CustomSpider import CustomSpider

class TuoitreSpider(CustomSpider):
    name = 'tuoitre'
    allowed_domains = ['tuoitre.vn']
    # start_urls = ['https://tuoitre.vn/thoi-su/xem-theo-ngay/02-11-2017.htm']
    # start_urls = ['https://tuoitre.vn/chien-si-cong-an-tra-lai-50-trieu-cua-roi-nhat-duoc-20171102221803983.htm']
    folder = 'data/tuoitre'
    date_url_format = '%Y-%m-%d'

    base_urls = [
        'https://tuoitre.vn/media/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/thoi-su/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/the-gioi/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/phap-luat/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/kinh-doanh/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/xe/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/nhip-song-tre/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/van-hoa/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/giai-tri/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/giao-duc/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/khoa-hoc/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/suc-khoe/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/gia-that/xem-theo-ngay/{}.htm',
        'https://tuoitre.vn/thu-gian/xem-theo-ngay/{}.htm'
    ]

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super(TuoitreSpider, self).__init__(from_date, to_date, *args, **kwargs)

    def start_requests(self):
        delta = timedelta(days=1)
        d = self.from_date
        while d <= self.to_date:
            date = d.strftime(self.date_format)
            for base_url in self.base_urls:
                url = base_url.format(date)
                yield scrapy.Request(url=url, callback=self.parse)

            d += delta

    def parse(self, response):
        news_urls = response.xpath('//div[@class="list-news-content"]/div/a/@href').extract()
        for url in news_urls:
            yield response.follow(url=url, callback=self.parse_news)


    def parse_news(self, response):
        title = response.css('h1.title-2::text').extract_first()
        title = self.remove_scpecial_characters(title)
        description = response.css('h2.txt-head::text').extract_first()
        description = self.remove_scpecial_characters(description)
        time = response.css('div.detail-content span.date::text').extract_first()
        time = self.normalizeTime(time)
        paragraphs = response.css('div.fck p').xpath('string(.)').extract()
        content = ' '.join(map(self.remove_scpecial_characters, paragraphs))

        self.write_to_file({'url': response.url, 'title': title, 'description': description, 
                            'time': time, 'content': content})

    def remove_scpecial_characters(self, str):
        return re.sub(r'[“”?!\n\r:;",.\t]+|<.*?>', ' ', str)

    def normalizeTime(self, raw_time_str):
        d = raw_time_str[:16]
        datetime_obj = datetime.strptime(d, '%d/%m/%Y %H:%M')
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
