# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
import pymongo
import os
import json
from scrapy.exceptions import DropItem
# from bson.objectid import ObjectId
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import csv
import os



class MongoDBUnitopPipeline:
    def __init__(self):
        
        mongo_host = os.getenv('MONGO_HOST', 'localhost')
        mongo_port = int(os.getenv('MONGO_PORT', 27017))
        self.client = pymongo.MongoClient(mongo_host, mongo_port)
        self.db = self.client['dbmycrawler']
        self.collection = self.db['tblunitop']
    
    def process_item(self, item, spider):
        
        try:
            self.collection.insert_one(dict(item))
            return item
        except Exception as e:
            spider.logger.error(f"Error inserting item into MongoDB: {e}")
            raise DropItem(f"Error inserting item: {e}")       
    
    def close_spider(self, spider):
        self.client.close()
           
class JsonDBUnitopPipeline:
    def __init__(self):
        self.file = open('jsondataunitop.json', 'a', encoding='utf-8')

    def process_item(self, item, spider):
        try:
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            self.file.write(line)
            return item
        except Exception as e:
            spider.logger.error(f"Error writing item to JSON file: {e}")
            raise

    def close_spider(self, spider):
        self.file.close()
class CSVDBUnitopPipeline:
    
    def __init__(self):
        self.file = open('csvdataunitop.csv', 'a', encoding='utf-8', newline='')
        self.writer = csv.writer(self.file, delimiter='$')

    def process_item(self, item, spider):
        try:
            self.writer.writerow([
                item.get('coursename', 'N/A'),
                item.get('lecturer', 'N/A'),
                item.get('intro', 'N/A'),
                item.get('describe', 'N/A'),
                item.get('courseUrl', 'N/A'),
                item.get('votenumber', 'N/A'),
                item.get('rating', 'N/A'),
                item.get('newfee', 'N/A'),
                item.get('oldfee', 'N/A'),
                item.get('lessonnum', 'N/A')
            ])
            return item
        except Exception as e:
            spider.logger.error(f"Error writing item to CSV file: {e}")
            raise

    def close_spider(self, spider):
        self.file.close()