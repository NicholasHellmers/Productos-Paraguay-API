package companies

import (
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gocolly/colly/v2"
)

type category struct {
	name string
	url  string
}

type Item struct {
	Name       string
	Price      string
	Category   string
	ProductUrl string
	ImageUrl   string
}

func Get_categories_stock() []category {
	var list_of_categories []category

	c := colly.NewCollector(
		colly.AllowedDomains("stock.com.py", "www.stock.com.py"),
	)

	c.OnHTML("li.inactive.level3", func(e *colly.HTMLElement) {
		selection := e.DOM
		category := category{
			name: selection.Find("a.collapsed").Text(),
			url:  selection.Find("a.collapsed").AttrOr("href", "")}
		list_of_categories = append(list_of_categories, category)

		// fmt.Println(selection.Find("a.collapsed").Text(), selection.Find("a.collapsed").AttrOr("href", ""))
		// fmt.Println("")
	})

	c.OnRequest(func(r *colly.Request) {
		fmt.Printf("Visiting: %s\n", r.URL)
	})

	c.OnError(func(_ *colly.Response, err error) {
		fmt.Printf("Something went wrong: %v \n", err)
	})

	c.Visit("https://www.stock.com.py/default.aspx")

	return list_of_categories
}

func Get_from_stock(category_name string, category_url string, acc int32) []Item {

	var list_of_items []Item

	c := colly.NewCollector(
		colly.AllowedDomains("stock.com.py", "www.stock.com.py"),
	)

	c.SetRequestTimeout(100 * time.Second)

	c.OnHTML("div.col-lg-2.col-md-3.col-sm-4.col-xs-6.producto", func(e *colly.HTMLElement) {
		selection := e.DOM
		item := Item{
			Name:       selection.Find("a.product-title-link").Text(),
			Price:      selection.Find("span.price-label").Text(),
			Category:   category_name,
			ProductUrl: selection.Find("a.product-title-link").AttrOr("href", ""),
			ImageUrl:   selection.Find("div.picture img").AttrOr("src", "")}
		// print item
		// fmt.Println(item.Name, item.Price, item.Category, item.ProductUrl, item.ImageUrl)
		item.Name = strings.ReplaceAll(item.Name, ",", ".")
		item.Price = strings.Replace(item.Price, "  ", "", 1)
		item.Price = strings.ReplaceAll(item.Price, ".", "")

		list_of_items = append(list_of_items, item)

		// fmt.Println("")
	})

	c.OnRequest(func(r *colly.Request) {
		fmt.Printf("Visiting: %s\n", r.URL)
	})

	c.OnError(func(_ *colly.Response, err error) {
		fmt.Printf("Something went wrong: %v \n", err)
	})

	c.Visit(category_url + "?pageindex=" + strconv.Itoa(int(acc)))

	return list_of_items
}

func Get_all_products_stock_helper(category_name string, category_url string, acc int32) []Item {
	var list_of_items []Item

	var items []Item = Get_from_stock(category_name, category_url, acc)

	if len(items) > 0 {
		list_of_items = append(list_of_items, items...)
		list_of_items = append(list_of_items, Get_all_products_stock_helper(category_name, category_url, acc+1)...)
	}

	return list_of_items
}

func removeDuplicates(elements []category) []category {
	// Use map to record duplicates as we find them.
	encountered := map[category]bool{}
	result := []category{}

	for _, e := range elements {
		if _, ok := encountered[e]; !ok {
			encountered[e] = true

			result = append(result, e)
		}
	}
	return result
}

func Get_all_products_stock() {

	// Get all categories
	var categories []category = Get_categories_stock()

	// Remove duplicates
	categories = removeDuplicates(categories)

	// only get first 10 categories
	// categories = categories[:10]

	fmt.Println(categories)

	channels := make([]chan []Item, 0)

	var items_wg sync.WaitGroup

	maxGoRoutines := 10

	guard := make(chan struct{}, maxGoRoutines)

	for _, category := range categories {
		guard <- struct{}{}

		items_wg.Add(1)

		time.Sleep(125 * time.Millisecond)

		channel := make(chan []Item)

		var list_of_items []Item

		go func(category_name string, category_url string) {
			list_of_items = append(list_of_items, Get_all_products_stock_helper(category_name, category_url, 1)...)
			defer items_wg.Done()
			<-guard
			channel <- list_of_items
		}(category.name, category.url)

		channels = append(channels, channel)

	}

	res := []Item{}

	for _, channel := range channels {
		res = append(res, <-channel...)
	}

	Write_data(res, "stock")

	fmt.Println("Finished scraping stock")

	items_wg.Wait()
}
