from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

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

class Product:
    def __init__(self, name, price, category, product_url, image_url):
        self.name = name
        self.price = price
        self.category = category
        self.product_url = product_url
        self.image_url = image_url

def construct_product(product: webdriver.remote.webelement.WebElement, category: str) -> (Product | None):
        product_media = product.find_element(By.CLASS_NAME, "thumbnail")
        product_body = product.find_element(By.CLASS_NAME, "media-body")

        new_product = Product(
            product_body.find_element(By.TAG_NAME, "a").get_attribute("textContent").strip(),
            product_body.find_element(By.CLASS_NAME, "single_add_to_cart_button.add_to_cart_button.add_to_cart_button_contado.button").text.strip(),
            category,
            product_media.find_element(By.TAG_NAME, "a").get_attribute("href"),
            product_media.find_element(By.TAG_NAME, "img").get_attribute("src")
        )

        # Remove "ver detalles" from the product name if present
        if "ver detalles" in new_product.name:
            new_product.name = new_product.name.replace("ver detalles", "").strip()

        # Remove \n from the product price if present
        if "\n" in new_product.price:
            new_product.price = new_product.price.replace("\n", "").strip()

        return new_product

def get_categories() -> (list[str] | None):
    '''
    Get the categories from the Tupi website
    
    '''
    service = Service(executable_path="./driver/chromedriver")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    start_time = time.time()

    driver.get("https://www.tupi.com.py/")

    categories = driver.find_elements(By.CLASS_NAME, "icon.tienesubmenu.icon-news")

    categories = [( category.get_attribute("textContent").strip(), category.get_attribute("href") ) for category in categories]
    categories = [category for category in categories if category[1] != ""]

    time.sleep(5)

    driver.quit()

    # remove entries where the url is empty

    print("Execution time: ", time.time() - start_time)

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
    while exit_condition == False:

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Check if there's an element with the tag "center" present
        load_animated_element = driver.find_elements(By.TAG_NAME, "center")

        if not load_animated_element:
            print("No hay mas productos por cargar")
            exit_condition = True
            break
        elif load_animated_element:
            print("Hay mas productos por cargar")
            time.sleep(7)
            continue

    products = driver.find_elements(By.CLASS_NAME, "product_unit.product.vista_")

    print(f"Category: {category}, products: {len(products)}")

    print("Execution time: ", time.time() - start_time)

    list_of_products = [ construct_product(product=product, category=category) for product in products ]

    driver.quit()

    return list_of_products

def main():
    # Get the categories and return them to the main function
    print("Getting categories...")
    categories = get_categories()
    print("There are ", len(categories), " categories")
    for category in categories:
        print(category)

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

    # Print the results of the threads onto a tupi.csv file
    print("Writing results to tupi.csv")
    df = pd.DataFrame([vars(product) for product in list_of_products])
    df.to_csv("./output/tupi.csv", index=False)
    
if __name__ == "__main__":
    main()