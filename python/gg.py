from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pandas as pd

from dataclasses import dataclass

import time

@dataclass(kw_only=True, slots=True)
class Product:
    name: str
    price: str
    category: str
    product_url: str
    image_url: str

def construct_product(product: webdriver.remote.webelement.WebElement) -> (Product | None):
    product_media = product.find_element(By.CLASS_NAME, "product-media")
    product_body = product.find_element(By.CLASS_NAME, "product-body")

    new_product = Product(
        name = product_body.find_element(By.CLASS_NAME, "product-title").text.strip(),
        price = product_body.find_element(By.CLASS_NAME, "new-price").text.strip(),
        category = product_body.find_element(By.CLASS_NAME, "product-cat").text.strip(),
        product_url = product_media.find_element(By.TAG_NAME, "a").get_attribute("href"),
        image_url = product_media.find_element(By.TAG_NAME, "img").get_attribute("src")
    )

    return new_product if new_product else None

def main():
    service = Service(executable_path="./driver/chromedriver")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("Headless Chrome Running")

    start_time = time.time()

    print("Consiguiendo productos de Gonzalez Gimenez")

    driver.get("https://www.gonzalezgimenez.com.py/buscador?q=&buscar=")

    exit_condition = False
    
    while exit_condition == False:
        # Find elements with class name of "infinite-status-prompt"
        # and print the attributes present in the elements
        elements = driver.find_elements(By.CLASS_NAME, "infinite-status-prompt")
        for element in elements:
            # print(element.get_attribute("outerHTML"))
            innerHTML = element.get_attribute("textContent").strip()
            style = element.get_attribute("style")

            if innerHTML == "- Se llegó al final de la lista -" and style.__contains__("display: none;"):
                # print("HAY MAS PRODUCTOS POR CARGAR")
                break

            elif innerHTML == "- Se llegó al final de la lista -" and not style.__contains__("display: none;"):
                print("NO HAY MAS PRODUCTOS POR CARGAR")

                # Now we can scan for products
                products = driver.find_elements(By.CLASS_NAME, "col-md-4.col-lg-4.col-xl-3.col-12")
                
                print("Cantidad de productos: ", len(products))

                list_of_products = [ construct_product(product=product) for product in products ]

                for product in list_of_products:
                    print(product)

                # write the products into a csv file called "gg_products.csv" in the output folder, if the file does not exist, it will be created
                df = pd.DataFrame(list_of_products)
                df.to_csv("./output/gg_products.csv", index=False)

                exit_condition = True
                break

        # Scroll to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    driver.quit()

    print("Execution time: ", time.time() - start_time)

if __name__ == "__main__":
    main()