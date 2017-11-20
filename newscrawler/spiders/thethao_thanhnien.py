# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import XPathSelector
import re
import json
import os
from datetime import datetime, timedelta, date
from .CustomSpider import CustomSpider

class ThethaoThanhnienSpider(CustomSpider):
    name = 'thethao.thanhnien'
    allowed_domains = ['thethao.thanhnien.vn']
    base_url = 'https://thethao.thanhnien.vn/sitemaps/news-{}.xml'
    folder = 'data/thanhnien'
    date_url_format = '%Y-%m-%d'

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super(ThethaoThanhnienSpider, self).__init__(from_date, to_date, *args, **kwargs)

        # if not os.path.exists(self.folder):
        #     os.makedirs(self.folder)

    def start_requests(self):
        now = datetime.now()
        current_month = now.strftime('%Y-%m')
        url = self.base_url.format(current_month)
        yield scrapy.Request(url=url, callback=self.parse_sitemap)

    def parse_sitemap(self, response):
        xml = XPathSelector(response)
        url_tags = xml.xpath('//urlset/url')
        for url_tag in url_tags:
            url = url_tag.xpath('./loc/text()').extract_first()
            date = url_tag.xpath('./lastmod/text()').extract_first()
            if not self.visited_url(url, date):
                yield scrapy.Request(url=url, meta={'date': date}, callback=self.parse_news)


    def parse_news(self, response):
        title = response.css('h1.cms-title::text').extract_first()
        title = self.remove_scpecial_characters(title)
        description =  response.css('div.cms-desc').xpath('string(.)').extract_first()  
        description = self.remove_scpecial_characters(description)
        paragraphs = response.xpath('//div[@class="cms-body"]/div[not(.//article) and not(.//table) and not(@class)]').xpath('string(.)').extract()
        content = ' '.join(map(self.remove_scpecial_characters, paragraphs))
        paragraphs = response.xpath('//div[@class="cms-body"]/p').xpath('string(.)').extract()
        content += ' ' + ' '.join(map(self.remove_scpecial_characters, paragraphs))

        self.write_to_file({'url': response.url, 'title': title, 'description': description, 
                            'date': response.meta['date'], 'content': content})

    def remove_scpecial_characters(self, str):
        return re.sub(r'[“”?!\n\r:;",.\t]+|<.*?>', ' ', str)

    def normalizeTime(self, raw_time_str):
        datetime_obj = datetime.strptime(raw_time_str, '%H:%M, %d/%m/%Y')
        return datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

    def visited_url(self, url, date):
        return False
        title = re.sub(r'[^A-Za-z0-9]', '_', url.split('/')[-1][:20])
        number = re.sub(r'[^0-9]', '', url)
        date = re.sub(r'[^0-9]', '_', date)
        folder = '{}/{}'.format(self.folder, date[:10])
        path = '{}/{}__{}.json'.format(folder, title, number)
        return os.path.exists(path)

    def write_to_file(self, data):
        title = re.sub(r'[^A-Za-z0-9]', '_', data['url'].split('/')[-1][:20])
        number = re.sub(r'[^0-9]', '', data['url'])
        date = re.sub(r'[^0-9]', '_', data['date'])
        folder = '{}/{}'.format(self.folder, date[:10])
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = '{}/{}__{}.json'.format(folder, title, number)
        with open(path, 'w', encoding="utf-8") as outfile:
            json.dump(data, outfile, ensure_ascii=False)

