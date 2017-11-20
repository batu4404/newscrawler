# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import XPathSelector
from newscrawler import settings
import json
import re
import os
from datetime import datetime, timedelta, date

class VnexpressSpider(scrapy.Spider):
    name = 'vnexpress'
    allowed_domains = ['vnexpress.net']
    date_format = '%d-%m-%Y'
    folder = 'data/vnexpress'
    base_url = 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y={}&m={}&d={}'

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super(VnexpressSpider, self).__init__(*args, **kwargs)

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
            url = self.base_url.format(d.year, d.month, d.day)
            yield scrapy.Request(url=url, callback=self.parse_sitemap)
            d += delta

    def parse_sitemap(self, response):
        xml = XPathSelector(response)
        urls = xml.xpath('//urlset/url')

        for url in urls:
            time = url.xpath('./news/publication_date/text()').extract_first()
            link = url.xpath('./loc/text()').extract_first()
            if self.visited_url(url=link, time=time):
                continue
                
            request = scrapy.Request(link, callback=self.parse_news)
            request.meta['link'] = link
            request.meta['time'] = re.sub(r'T', ' ', time[:19])
            yield request

    def parse_news(self, response):
        title = response.css('h1.title_news_detail')[0].xpath('text()').extract_first()
        title = self.remove_scpecial_characters(title)
        description = response.css('h2.description')[0].xpath('text()').extract_first()
        description = self.remove_scpecial_characters(description)
        paragraphs = response.css('article.content_detail>p:not(.Image)::text').extract()
        content = ' '.join(map(self.remove_scpecial_characters, paragraphs))
    
        self.write_to_file({'url': response.meta['link'], 'title': title, 
                            'description': description, 'time': response.meta['time'],
                            'content': content})

    def remove_scpecial_characters(self, str):
        return re.sub(r'[“”?!\r\n:;",.\t]+|<.*?>', ' ', str)

    def visited_url(self, url, time):
        title = re.sub(r'[^A-Za-z0-9]', '_', url.split('/')[-1][:20])
        time = re.sub(r'[^0-9]', '_', time)
        folder = '{}/{}'.format(self.folder, time[:10])
        file_name = '{}/{}__{}.json'.format(folder, title, time)
        return os.path.exists(file_name)

    def write_to_file(self, data):
        title = re.sub(r'[^A-Za-z0-9]', '_', data['url'].split('/')[-1][:20])
        time = re.sub(r'[^0-9]', '_', data['time'])
        folder = '{}/{}'.format(self.folder, time[:10])
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = '{}/{}__{}.json'.format(folder, title, time)
        with open(file_name, 'w', encoding="utf-8") as outfile:
            json.dump(data, outfile, ensure_ascii=False)

