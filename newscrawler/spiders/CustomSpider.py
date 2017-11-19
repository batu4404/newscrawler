# -*- coding: utf-8 -*-
import scrapy
import os
import re
import json
from datetime import datetime, timedelta, date

class CustomSpider(scrapy.Spider):
    date_format = '%d-%m-%Y'

    def __init__(self, from_date=None, to_date=None, *args, **kwargs):
        super(CustomSpider, self).__init__(*args, **kwargs)

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


    def write_to_file(self, data):
        title = re.sub(r'[^0-9]', '', data['url'])
        time = re.sub(r'[^0-9]', '_', data['time'])
        folder = self.folder + '/' + time[:10]
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_name = '{}/{}__{}.json'.format(folder, title, time)
        with open(file_name, 'w', encoding="utf-8") as outfile:
            json.dump(data, outfile, ensure_ascii=False)