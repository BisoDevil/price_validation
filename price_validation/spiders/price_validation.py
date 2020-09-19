import scrapy
from fuzzywuzzy import fuzz
import operator


class PriceValidation(scrapy.Spider):
    name = "price"
    allowed_domains = ["noon.com", "souq.com", "jumia.com.eg", 'btech.com']
    keywords = [

    ]

    def __init__(self, data='', *args, **kwargs):
        super(PriceValidation, self).__init__(*args, **kwargs)
        self.keywords = data.split('=')

    def start_requests(self):
        for key in self.keywords:
            link = "https://egypt.souq.com/eg-en/"+key + \
                "/mobile-phones-33/a-t/s/?section=2&page=1"
            yield scrapy.Request(link, callback=self.parse,
                                 meta={'key': key},)

    def parse(self, response):
        item = {}
        key = response.meta['key']
        # links = response.xpath(
        #     "//div[@class='columns small-7 medium-12']//a//@href|//a[contains(@id,'quickview')]/@href|//div[@class='col col-info item-content']/a/@href|//div[@class='columns small-8 medium-12']/ul[@class='body no-bullet']//@href").extract()
        titles = response.xpath(
            "//a[@class='itemLink sk-clr2 sPrimaryLink']/h1[@class='itemTitle']/text()").extract()
        prices = response.xpath("//h3[@class='itemPrice']/text()").extract()

        if len(titles) > 0:
            item_link = self.get_best_match_title(
                titles=titles, key=key, prices=prices)
            item["key"] = key
            item["souq_title"] = ''.join(item_link.split(':')[0]).strip()
            item["souq_price"] = ''.join(item_link.split(':')[1]).strip()
        else:
            item["key"] = key
            item["souq_title"] = ''
            item["souq_price"] = ''
        link = "https://www.noon.com/egypt-en/electronics-and-mobiles/mobiles-and-accessories/mobiles-20905/smartphones?q="+key
        yield scrapy.Request(link, callback=self.parse_noon, meta={'key': key, 'item': item})

    def parse_noon(self, response):
        key = response.meta['key']
        item = response.meta['item']
        titles = response.xpath(
            "//div[@class='jsx-564649128 wrapper gridView ']/a[@class='jsx-564649128 product']/div[@class='jsx-564649128 detailsContainer']/div[@class='jsx-564649128 name']/div/span//text()").extract()
        prices = response.xpath(
            "//div[@class='jsx-564649128 priceRow']/p[@class='jsx-4251264678 price']/span[@class='jsx-4251264678 sellingPrice']/span/span[@class='value']//text()").extract()
        if len(titles) > 0:
            item_link = self.get_best_match_title(
                titles=titles, key=key, prices=prices)
            item["key"] = key
            item["noon_title"] = ''.join(item_link.split(':')[0]).strip()
            item["noon_price"] = ''.join(item_link.split(':')[1]).strip()
        else:
            item["key"] = key
            item["noon_title"] = ''
            item["noon_price"] = ''
        link = "https://www.jumia.com.eg/mobile-phones/?q="+key
        yield scrapy.Request(link, callback=self.parse_jumia, meta={'key': key, 'item': item})

        # https://www.jumia.com.eg/phones-tablets/?q=samsung+galaxy+m31

    def parse_jumia(self, response):
        key = response.meta['key']
        item = response.meta['item']
        titles = response.xpath(
            "//a[@class='core']/div[@class='info']/h3[@class='name']//text()").extract()
        prices = response.xpath(
            "//a[@class='core']/div[@class='info']/div[@class='prc']//text()").extract()
        if len(titles) > 0:
            item_link = self.get_best_match_title(
                titles=titles, key=key, prices=prices)
            item["key"] = key
            item["jumia_title"] = ''.join(item_link.split(':')[0]).strip()
            item["jumia_price"] = ''.join(item_link.split(':')[1]).strip()
        else:
            item["key"] = key
            item["jumia_title"] = ''
            item["jumia_price"] = ''
        link = "https://btech.com/en/catalogsearch/result/?cat=49&q="+key
        yield scrapy.Request(link, callback=self.parse_btech, meta={'key': key, 'item': item})
        # https://btech.com/en/catalogsearch/result/?cat=49&q=

    def parse_btech(self, response):
        key = response.meta['key']
        item = response.meta['item']
        titles = response.xpath(
            "//strong[@class='product name product-item-name']/a[@class='product-item-link']//text()").extract()
        prices = response.xpath(
            "//div[@class='cash']/span[@class='as-badge']//text()").extract()
        if len(titles) > 0:
            item_link = self.get_best_match_title(
                titles=titles, key=key, prices=prices)
            item["key"] = key
            item["btech_title"] = ''.join(item_link.split(':')[0]).strip()
            item["btech_price"] = ''.join(item_link.split(':')[1]).strip()
        else:
            item["key"] = key
            item["btech_title"] = ''
            item["btech_price"] = ''
        yield item

    def get_best_match_title(self, titles, key, prices):
        acceptedLinks = {}
        for title,  price in zip(titles, prices):
            token_sort = fuzz.token_sort_ratio(key, title)
            token_set = fuzz.token_set_ratio(key, title)
            partial_set = fuzz.partial_token_set_ratio(key, title)
            score = (token_set+token_sort+partial_set)/3
            if score > 80:
                price_int = price.replace('EGP', "").replace(",", '').strip()
                t = title+":"+price_int
                acceptedLinks[t] = score
        if len(acceptedLinks) > 0:
            itemLink = max(acceptedLinks.items(),
                           key=operator.itemgetter(1))[0]
        else:
            itemLink = 'weak:match'

        return itemLink
