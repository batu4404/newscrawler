# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import XPathSelector
from newscrawler import settings
import json
import re
import os
from datetime import datetime

class VnexpressSpider(scrapy.Spider):
    name = 'vnexpress'
    allowed_domains = ['vnexpress.net']
    year = 2017

    def __init__(self, only_day=True, day=None, month=None, year=None, *args, **kwargs):
        super(VnexpressSpider, self).__init__(*args, **kwargs)
        now = datetime.now()
        self.day = self.conditional(day != None, day, now.day)
        self.month = self.conditional(month != None, month, now.month)
        self.year = self.conditional(year != None, year, now.year)
        self.only_day = only_day

    def conditional(self, condition, exp1, exp2):
        if condition:
            return exp1
        else:
            return exp2

    # start_urls = ['https://vnexpress.net/tin-tuc/khoa-hoc/trong-nuoc/su-kien-trinh-dien-cong-nghe-lon-nhat-nam-se-dien-ra-tai-da-nang-3671585.html'] 

    # start_urls = ['https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y=2017&m=11&d=03',
    #                 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y=2017&m=11&d=02',
    #                 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y=2017&m=11&d=01',
    #                 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y=2017&m=10&d=31',
    #                 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y=2017&m=10&d=30',
    #                 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y=2017&m=10&d=29',
    #                 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y=2017&m=10&d=28']
    def start_requests(self):
        base_url = 'https://vnexpress.net/sitemap/1000000/sitemap-news.xml?y={}&m={}&d={}'
        if self.only_day:
            url = base_url.format(str(self.year), str(self.month).zfill(2), str(self.day).zfill(2))
            yield scrapy.Request(url=url, callback=self.parse)
            return
       
        urls = []
        for m in range(9, 11):
            for d in range(1, 32):
                url = base_url.format(str(self.year), str(m).zfill(2), str(d).zfill(2))
                urls.append(url)
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
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
        article_content = response.css('article.content_detail')
        content = ''
        if (len(article_content) > 0):
            paragraphs = article_content.css('p:not(.Image)')
            for p in paragraphs:
                text = p.xpath('text()').extract_first()
                if text != None:
                    content += self.remove_scpecial_characters(text)
        
        # content = content.strip()

        # print(title)
        self.write_to_file({'url': response.meta['link'], 'title': title, 
                            'description': description, 'time': response.meta['time'],
                            'content': content})

    def remove_scpecial_characters(self, str):
        return re.sub(r'[\n:;",.\t]+|<.*?>', ' ', str)

    def visited_url(self, url, time):
        title = re.sub(r'[^A-Za-z0-9]', '_', url.split('/')[-1][:20])
        time = re.sub(r'[^0-9]', '_', time)
        folder = 'data/' + time[:10]
        file_name = folder + '/' + title + '__' + time + '.json'
        return os.path.exists(folder)

    def write_to_file(self, data):
        title = re.sub(r'[^A-Za-z0-9]', '_', data['url'].split('/')[-1][:20])
        time = re.sub(r'[^0-9]', '_', data['time'])
        folder = 'data/' + time[:10]
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = folder + '/' + title + '__' + time + '.json'
        with open(file_name, 'w', encoding="utf-8") as outfile:
            json.dump(data, outfile, ensure_ascii=False)

