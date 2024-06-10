package companies

import (
	"os"
	"strings"
)

func Write_data(list_of_items []Item, company string) {

	// append contents of stock to a file in a folder called "data"
	f, err := os.OpenFile("./output/data/products_"+company+".csv", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	if err != nil {
		panic(err)
	}

	f.WriteString("name,price,category,product_url,image_url,supermarket\n")
	for _, item := range list_of_items {
		// replace commas in name, Price, Category, with periods
		item.Name = strings.ReplaceAll(item.Name, ",", ".")
		item.Price = strings.ReplaceAll(item.Price, ",", ".")
		item.Category = strings.ReplaceAll(item.Category, ",", ".")

		// Make all text lowercase
		item.Name = strings.ToLower(item.Name)
		item.Category = strings.ToLower(item.Category)

		// Trun whitespace larger than 1 to 1
		item.Name = strings.ReplaceAll(item.Name, "  ", " ")

		f.WriteString(item.Name + "," + item.Price + "," + item.Category + "," + item.ProductUrl + "," + item.ImageUrl + "," + company + "\n")
	}
	f.Close()

}
