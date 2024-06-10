package companies

import (
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gocolly/colly/v2"
)

func Get_categories_superseis() []category {
	var list_of_categories []category

	c := colly.NewCollector(
		colly.AllowedDomains("superseis.com.py", "www.superseis.com.py"),
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

	c.Visit("https://www.superseis.com.py/default.aspx")

	return list_of_categories
}

func Get_from_superseis(category_name string, category_url string, acc int32) []Item {

	var list_of_items []Item

	c := colly.NewCollector(
		colly.AllowedDomains("superseis.com.py", "www.superseis.com.py"),
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

		item.Name = strings.ReplaceAll(item.Name, ",", ".")
		item.Price = strings.Replace(item.Price, "  ", "", 1)
		item.Price = strings.ReplaceAll(item.Price, ".", "")

		// print item
		// fmt.Println(item.Name, item.Price, item.Category, item.ProductUrl, item.ImageUrl)
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

func Get_all_products_superseis_helper(category_name string, category_url string, acc int32) []Item {
	var list_of_items []Item

	var items []Item = Get_from_superseis(category_name, category_url, acc)

	if len(items) > 0 {
		list_of_items = append(list_of_items, items...)
		list_of_items = append(list_of_items, Get_all_products_superseis_helper(category_name, category_url, acc+1)...)
	}

	return list_of_items
}

func Get_all_products_superseis() {

	// Get all categories
	var categories []category = Get_categories_superseis()

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
			list_of_items = append(list_of_items, Get_all_products_superseis_helper(category_name, category_url, 1)...)
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

	Write_data(res, "superseis")

	fmt.Println("Finished scraping superseis")

	items_wg.Wait()
}
