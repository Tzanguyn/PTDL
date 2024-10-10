import scrapy
import os
from scrapy.crawler import CrawlerProcess
from pymongo import MongoClient

class RugSpider(scrapy.Spider):
    name = 'rug_spider'
    start_page = 1
    max_pages = 134

    def start_requests(self):
        yield scrapy.Request(
            f'https://www.therugshopuk.co.uk/rugs-by-type/rugs.html?page={self.start_page}',
            meta={'page': self.start_page}
        )

    def parse(self, response):
        # Xử lý sản phẩm trên trang hiện tại
        products = response.css('div.product-item-info')
        for product in products:
            product_link = product.css('a.product-item-link::attr(href)').get()
            product_data = {
                'Name': product.css('img.product-image-photo.image::attr(alt)').get(default='N/A').strip(),
                'Old_Price': self.clean_price(product.css('span.old-price span.price::text').get(default='N/A').strip()),
                'Special_Price': self.clean_price(product.css('span.special-price span.price::text').get(default='N/A').strip()),
                'Save': self.clean_save_percentage(product.css('span.save-percentage::text').get(default='N/A').strip()),
            }
            if product_link:
                yield response.follow(product_link, self.parse_product, meta={'product_data': product_data})

        # Lấy trang hiện tại từ meta
        current_page = response.meta.get('page', 1)

        # Tìm link của trang kế tiếp
        next_page = response.css('a.next::attr(href)').get()

        # Nếu có trang kế tiếp và chưa đạt số trang tối đa
        if next_page and current_page < self.max_pages:
            yield response.follow(next_page, callback=self.parse, meta={'page': current_page + 1})

    def parse_product(self, response):
        product_data = response.meta['product_data']

        # Truy cập phần 'Key Features'
        features = response.css('div.tab ul.as-list li')

        # Lấy thông tin chi tiết của sản phẩm
        for feature in features:
            text = feature.css('span::text').get(default='').strip()
            if "Material" in text:
                product_data['Material'] = feature.css('span.prod_mat::text').get(default='N/A').strip()
            elif "Cleaning Process" in text:
                product_data['Cleaning_Process'] = feature.css('::text').extract()[-1].strip()
            elif "Pattern" in text:
                product_data['Pattern'] = feature.css('::text').extract()[-1].strip()
            elif "Pile height" in text:
                pile_height_raw = feature.css('::text').extract()[-1].strip()
                product_data['Pile_height'] = self.clean_pile_height(pile_height_raw)
            elif "Weight" in text:
                weight_raw = feature.css('::text').extract()[-1].strip()
                product_data['Weight'] = self.clean_weight(weight_raw)
            elif "Origin" in text:
                product_data['Origin'] = feature.css('::text').extract()[-1].strip()
            elif "Type" in text:
                product_data['Type'] = feature.css('::text').extract()[-1].strip()

        reviews = response.css('div.rrrr')
        review_texts = []
        for review in reviews:
            review_message = review.css('div.reviewmsg::text').get(default='N/A')
            review_texts.append(f"{review_message}")
        
        product_data['Product_Reviews'] = ' | '.join(review_texts)

        # Lưu dữ liệu vào MongoDB
        self.collection.insert_one(product_data)
        # Kiểm tra dữ liệu đã lấy
        yield product_data

    def clean_price(self, price_str):
        """Hàm này sẽ làm sạch chuỗi giá và chuyển đổi thành số."""
        if price_str and price_str != 'N/A':
            # Xóa ký hiệu £ và chuyển đổi thành số
            return float(price_str.replace('£', '').replace(',', '').strip())
        return None

    def clean_save_percentage(self, save_str):
        """Làm sạch chuỗi Save, chỉ giữ lại số phần trăm mà không có dấu %."""
        if save_str and save_str != 'N/A':
            # Xóa dấu % và chỉ giữ lại số
            return save_str.replace('%', '').strip()
        return None

    def clean_pile_height(self, pile_height_str):
        """Làm sạch cột Pile_height, lấy giá trị số và chuyển đổi đơn vị nếu cần."""
        if pile_height_str:
            # Giả sử dữ liệu luôn có dạng '45mm' hoặc '4.5cm'
            pile_height_num = ''.join([c for c in pile_height_str if c.isdigit() or c == '.'])
            if 'mm' in pile_height_str:
                return float(pile_height_num)  # Giữ nguyên mm
            elif 'cm' in pile_height_str:
                return float(pile_height_num) * 10  # Chuyển đổi từ cm sang mm
        return None

    def clean_weight(self, weight_raw):
        if weight_raw:  # Kiểm tra xem weight_raw có giá trị không
            weight_num = ''.join(filter(str.isdigit, weight_raw))  # Lọc ra chỉ số
        if weight_num:  # Kiểm tra xem weight_num có giá trị không
            return int(weight_num)  # Trả về giá trị số, giữ nguyên GSM
        return None  # Nếu không có giá trị phù hợp, trả về None hoặc giá trị mặc định

    

# Sau đó tiếp tục các thao tác khác với product_data


    def close(self, reason):
        if self.items:
            try:
                self.collection.insert_many(self.items)
            except Exception as e:
                self.logger.error(f"Error inserting data into MongoDB: {e}")
        self.client.close()


# Setup CrawlerProcess and start the spider
process = CrawlerProcess(settings={
    'FEED_URI': 'data.csv',
    'FEED_FORMAT': 'csv',
    'LOG_LEVEL': 'INFO',
    'DOWNLOAD_DELAY': 0,
})

process.crawl(RugSpider)
process.start()
