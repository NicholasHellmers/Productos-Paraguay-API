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
        product_media = product.find_elements(By.CLASS_NAME, "img")
        
        if len(product_media) > 0:
            product_images = product_media[0].find_elements(By.TAG_NAME, "img")
        else:
            print("There's an error at product_media")
            return None

        product_body = product.find_element(By.CLASS_NAME, "info")

        if len(product_media) > 0:
            new_product = Product(
                name = product_body.find_element(By.TAG_NAME, "a").get_attribute("textContent").strip(),
                price = product_body.find_element(By.CLASS_NAME, "monto").text.strip(),
                category = category,
                product_url = product_media[ len(product_media)  - 1 ].get_attribute("href"),
                image_url = product_images[ len(product_images) - 1 ].get_attribute("src")
            )
        else:
            name = product_body.find_element(By.TAG_NAME, "a").get_attribute("textContent").strip()
            print(f"There's an error at {name} product")
            return None

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

    driver.get("https://www.bristol.com.py/")

    categories = driver.find_elements(By.CLASS_NAME, "cols2")

    categories = categories[0].find_elements(By.CLASS_NAME, "hdr")
    
    categories = [ (category.find_element(By.TAG_NAME, "a").get_attribute("textContent").strip(), category.find_element(By.TAG_NAME, "a").get_attribute("href")) for category in categories ]

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

        # Find the button with id "catalogoPaginado", if present, it means that there are more products to load
        paginadoCheck = driver.find_element(By.ID, "catalogoPaginado").find_element(By.CLASS_NAME, "txt")

        load_check = paginadoCheck.find_elements(By.TAG_NAME, "span")

        bounds = [ int(load.get_attribute("textContent").strip()) for load in load_check ]

        print(bounds)

        # If there is a button, scroll down
        if bounds[1] - bounds[0] > 0:
            print("there are more products to load")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        else:
            print(f"no more products to load for category {category}")
            exit_condition = True

    product_view = driver.find_element(By.ID, "catalogoProductos")

    products = product_view.find_elements(By.CLASS_NAME, "cnt")

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

    # Launch a thread function for each category
    # and return the results to the main function
    print("Launching threads...")
    threads = []
    # Remove category with url "https://www.bristol.com.py/catalogo?tipo=tecnologia-ai"
    categories = [ category for category in categories if category[1] != "https://www.bristol.com.py/catalogo?tipo=tecnologia-ai" ]
    for category in categories:
        thread = ThreadWithReturnValue(target=thread_function, args=(category[0], category[1]))
        thread.start()
        threads.append(thread)

    # Wait for the threads to finish
    print("Waiting for threads to finish...")
    list_of_products = []
    for thread in threads:
        if thread.join() is not None:
            list_of_products += thread.join()
        else:
            print(f"There was an error with the thread {thread}")

    # Print the results of the threads onto a tupi.csv file
    print("Writing results to bristol.csv")
    df = pd.DataFrame(list_of_products)
    # Remove duplicates
    df.drop_duplicates(subset=["name"], keep="first", inplace=True)
    df.to_csv("./output/bristol.csv", index=False)
    
if __name__ == "__main__":
    main()