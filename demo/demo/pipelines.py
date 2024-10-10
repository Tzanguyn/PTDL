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



class MongoDBRugsPipeline:
    def __init__(self):
        
        self.client = pymongo.MongoClient('mongodb://192.168.1.8:27017')
        self.db = self.client['rugs']
        self.collection = self.db['rug_collection']
        self.items = []
    
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
    def process_item(self, item, spider):
        with open('data.json', 'a', encoding='utf-8') as file:
            line = json.dumps(dict(item), ensure_ascii=False) + '\n'
            file.write(line)
        return item

    
class CSVDBUnitopPipeline:
    

    def process_item(self, item, spider):
        with open('data.csv', 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter=',')
            writer.writerow([
                item['Name'],
                item['Old_Price'],
                item['Special_Price'],
                item['Save'],
                item['Material'],
                item['Cleaning_Process'],
                item['Pattern'],
                item['Pile_height'],
                item['Weight'],
                item['Origin'],
                item['Type'],
                item['Product_Reviews'],
            
            ])
        return item