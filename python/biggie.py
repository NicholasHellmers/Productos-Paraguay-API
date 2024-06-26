from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from dataclasses import dataclass

import threading as th

import pandas as pd

import time

class ThreadWithReturnValue(th.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        th.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        th.Thread.join(self)
        return self._return

@dataclass(kw_only=True, slots=True)
class Product:
    name: str
    price: str
    category: str
    product_url: str
    image_url: str

def construct_product(product: webdriver.remote.webelement.WebElement, category: str) -> (Product | None):
        product_image = product.find_element(By.CLASS_NAME, "v-image__image.v-image__image--contain")

        product_name = product.find_element(By.CLASS_NAME, "v-card__title.titleCard.pt-1")

        product_price = product.find_element(By.CLASS_NAME, "v-card__text.title.font-weight-medium.pa-0.d-flex.justify-center")

        def parse_style(style: str) -> str:
            '''
            This function will parse the inline style of the div containing the product image, and return the url of the image as an str
            '''
            parsed_style = style.split(";")

            parsed_style_url = parsed_style[0].replace("background-image: url(\"", "").replace("\")", "")

            # print(parsed_style_url)

            return parsed_style_url

        new_product = Product(
            name = product_name.get_attribute("textContent").strip(),
            price = product_price.get_attribute("textContent").split("₲")[1].strip().replace(".", ""),
            category = category,
            product_url = "https://biggie.com.py/search?q=" + product_name.get_attribute("textContent").strip().replace(" ", "%20"),
            image_url = parse_style(product_image.get_attribute("style"))
        )

        return new_product

def get_categories() -> (list[str] | None):
    '''
    Get the categories from the biggie website
    
    '''
    service = Service(executable_path="./driver/chromedriver")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    start_time = time.time()

    driver.get("https://biggie.com.py/products")

    time.sleep(4)

    categories = driver.find_elements(By.CLASS_NAME, "mb-7.rowItem")

    categories = [ (category.get_attribute("textContent").strip(), category.find_element(By.TAG_NAME, "a").get_attribute("href")) for category in categories ]
    categories = [category for category in categories if category[1] != ""]


    driver.quit()

    # remove entries where the url is empty

    print("Execution time: ", time.time() - start_time)

    for category in categories:
        print(category)

    return categories


def thread_function(category: str, url: str, ) -> (list[Product] | None):
    '''
    This function will be used to run the scraping process in parallel
    and return the results to the main function
    '''
    print(f"Scraping category: {category}, url: {url}")

    service = Service(executable_path="./driver/chromedriver")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    start_time = time.time()

    driver.get(url)

    exit_condition = False

    tmp_products = []

    list_of_products = []

    while exit_condition == False:

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(5)


        # Check if there's an element with the tag "v-pagination__navigation" present
        # This is the button that is in charge of pagination
        pagination_buttons = driver.find_elements(By.CLASS_NAME, "v-pagination__navigation")

        next_button = pagination_buttons[1]

        tmp_products = driver.find_elements(By.CLASS_NAME, "content")

        list_of_products.append([ construct_product(product=product, category=category) for product in tmp_products ])

        print(f"Category: {category}, page: {len(list_of_products)}")
        
        if next_button.get_attribute("disabled"):
            exit_condition = True
        else:
            next_button.click()
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


    # flatten the products to load
    list_of_products = [product for products in list_of_products for product in products]

    print(f"Category: {category}, products: {len(list_of_products)}")

    print("Execution time: ", time.time() - start_time)


    driver.quit()

    return list_of_products

def main():
    # Get the categories and return them to the main function
    print("Getting categories...")
    categories = get_categories()
    print("There are ", len(categories), " categories")

    # Launch a thread function for each category
    # and return the results to the main function
    print("Launching threads...")
    threads = []
    for category in categories:
        thread = ThreadWithReturnValue(target=thread_function, args=(category[0], category[1]))
        thread.start()
        threads.append(thread)

    # Wait for the threads to finish
    print("Waiting for threads to finish...")
    list_of_products = []
    for thread in threads:
        list_of_products += thread.join()

    # Print the results of the threads onto a biggie.csv file
    print("Writing results to biggie.csv")
    df = pd.DataFrame(list_of_products)
    # Remove duplicates
    df.drop_duplicates(subset=["name"], keep="first", inplace=True)
    df.to_csv("./output/biggie.csv", index=False)
    
if __name__ == "__main__":
    main()