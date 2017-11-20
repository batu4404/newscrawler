# -*- coding: utf-8 -*-
import scrapy
import re
import json
import os
from datetime import datetime, timedelta, date
from .CustomSpider import CustomSpider

class ThanhnienSpider(CustomSpider):
    name = 'thanhnien'
    allowed_domains = ['thanhnien.vn']
    base_urls = ['https://thanhnien.vn/thoi-su/{}/',
                'https://thanhnien.vn/the-gioi/{}/',
                'https://thanhnien.vn/van-hoa/{}/',
                'https://thanhnien.vn/toi-viet/{}/',
                'https://thanhnien.vn/doi-song/{}/',
                'https://thanhnien.vn/kinh-doanh/{}/',
                'https://thanhnien.vn/gioi-tre/{}/',
                'https://thanhnien.vn/giao-duc/{}/',
                'https://thanhnien.vn/cong-nghe/{}/',
                'https://thanhnien.vn/suc-khoe/{}/' ]
    folder = 'data/thanhnien'
    date_url_format = '%Y-%m-%d'

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super(ThanhnienSpider, self).__init__(from_date, to_date, *args, **kwargs)

        # if not os.path.exists(self.folder):
        #     os.makedirs(self.folder)

    def start_requests(self):
        delta = timedelta(days=1)
        d = self.from_date
        while d <= self.to_date:
            date = d.strftime(self.date_url_format)
            for base_url in self.base_urls:
                url = base_url.format(date)
                yield scrapy.Request(url=url, callback=self.parse)
            d += delta

    def parse(self, response):
        for r in self.parse_articles(response):
            yield r
        
        pagination = response.css('div#paging li a:not([class])::attr(href)').extract()
        for p in pagination:
            yield response.follow(url=p, callback=self.parse_articles)


    def parse_articles(self, response):
        articles = response.css('section.tag-content > article')
        for article in articles:
            url = article.css('h2 a::attr(href)').extract_first()
            time = article.css('time::text').extract_first()
            time = self.normalizeTime(time)
            if not self.visited_url(url, time):
                yield response.follow(url=url, meta={'time': time}, callback=self.parse_news)


    def parse_news(self, response):
        title = response.css('h1.cms-title::text').extract_first()
        title = self.remove_scpecial_characters(title)
        description =  response.css('div.cms-desc').xpath('string(.)').extract_first()  
        description = self.remove_scpecial_characters(description)
        paragraphs = response.xpath('//div[@class="cms-body"]/div[not(.//article) and not(.//table) and not(@class)]').xpath('string(.)').extract()
        content = ' '.join(map(self.remove_scpecial_characters, paragraphs))
        paragraphs = response.xpath('//div[@class="cms-body"]/p').xpath('string(.)').extract()
        content = ' '.join(map(self.remove_scpecial_characters, paragraphs))

        self.write_to_file({'url': response.url, 'title': title, 'description': description, 
                            'time': response.meta['time'], 'content': content})

    def remove_scpecial_characters(self, str):
        return re.sub(r'[“”?!\n\r:;",.\t]+|<.*?>', ' ', str)

    def normalizeTime(self, raw_time_str):
        datetime_obj = datetime.strptime(raw_time_str, '%H:%M, %d/%m/%Y')
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

