import scrapy
import os 
from scrapy.crawler import CrawlerProcess
from pymongo import MongoClient

class RugSpider(scrapy.Spider):
    name = 'rug'
    
    start_page = 1
    max_pages = 134

    def __init__(self, *args, **kwargs):
        mongo_host = os.getenv('MONGO_HOST', 'localhost')
        mongo_port = int(os.getenv('MONGO_PORT', 27017))
        self.client = MongoClient(mongo_host, mongo_port)
        self.db = self.client['rug_demo']
        self.collection = self.db['rug_collection']
        self.items = []

    def start_requests(self):
        yield scrapy.Request(f'https://www.therugshopuk.co.uk/rugs-by-type/rugs.html?page={self.start_page}')   

    def parse(self, response):
        products = response.css('div.product-item-info')
        for product in products:
            product_link = product.css('a.product-item-link::attr(href)').get()
            product_data = {
                'Name': product.css('img.product-image-photo.image::attr(alt)').get(default='N/A'),
                'Price': product.css('span.price::text').get(default='N/A'),
                'Material': product.css('ul.as-list>li::text').get(default='N/A'),
                'Sizes': product.css('div.conf-sizeav span.confsizlist::text').get(default='N/A'),
                'Save': product.css('span.save-percentage::text').get(default='N/A'),
                'Cleaning Process': product.css('ul.as-list>li:nth-of-type(2)::text').get(default='N/A'),
                'Pattern': product.css('ul.as-list>li:nth-of-type(3)::text').get(default='N/A'),
                'Weight': product.css('ul.as-list>li:nth-of-type(4)::text').get(default='N/A'),
                'Backing': product.css('ul.as-list>li:nth-of-type(5)::text').get(default='N/A'),
                'Origin': product.css('ul.as-list>li:nth-of-type(6)::text').get(default='N/A'),
                'Type': product.css('ul.as-list>li:nth-of-type(7)::text').get(default='N/A'),
                'Pile height': product.css('ul.as-list>li:nth-of-type(8)::text').get(default='N/A'),
            }
            if product_link:
                yield response.follow(product_link, self.parse_product, meta={'product_data': product_data})

        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        product_data = response.meta['product_data']
        reviews = response.css('div.rrrr')
        review_texts = []
        for review in reviews:
            review_message = review.css('div.reviewmsg::text').get(default='N/A')
            review_texts.append(f"{review_message}")
        
        product_data['Product Reviews'] = ' | '.join(review_texts)
        self.items.append(product_data)

    def close(self, reason):
        if self.items:
            try:
                self.collection.insert_many(self.items)
            except Exception as e:
                self.logger.error(f"Error inserting data into MongoDB: {e}")
        self.client.close()
        
process = CrawlerProcess(settings={
    'FEED_URI': 'data.csv',
    'FEED_FORMAT': 'csv',
    'LOG_LEVEL': 'INFO',
    'DOWNLOAD_DELAY': 0,
})

process.crawl(RugSpider)
process.start()