package companies

import (
	"fmt"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

func Get_from_arete(acc int) []Item {

	var list_of_items []Item

	c := colly.NewCollector(
		colly.AllowedDomains("arete.com.py", "www.arete.com.py"),
	)

	c.SetRequestTimeout(100 * time.Second)

	c.OnHTML("div.product", func(e *colly.HTMLElement) {
		selection := e.DOM
		item := Item{
			Name:       selection.Find("h2.ecommercepro-loop-product__title").Text(),
			Price:      selection.Find("span.amount").Text(),
			Category:   "",
			ProductUrl: "https://arete.com.py/" + selection.Find("a.ecommercepro-LoopProduct-link").AttrOr("href", ""),
			ImageUrl:   selection.Find("img").AttrOr("data-src", ""),
		}

		// If Price contains "OFERTA" then remove it
		if strings.Contains(item.Price, "OFERTA") {
			item.Price = strings.Replace(item.Price, "OFERTA₲. ", "", 1)
			item.Price = strings.ReplaceAll(item.Price, "₲.", "")
			item.Price = strings.ReplaceAll(item.Price, ".", "")
			split := strings.Split(item.Price, " ")
			item.Price = split[0]
		} else {
			item.Price = strings.Replace(item.Price, "₲. ", "", 1)
			item.Price = strings.ReplaceAll(item.Price, ".", "")
		}

		list_of_items = append(list_of_items, item)
	})

	c.OnRequest(func(r *colly.Request) {
		fmt.Printf("Visiting: %s\n", r.URL)
	})

	c.OnError(func(_ *colly.Response, err error) {
		fmt.Printf("Something went wrong: %v \n", err)
	})

	c.Visit("https://arete.com.py/productos." + strconv.Itoa(acc))

	return list_of_items
}

func Get_total_number_of_pages_arete() int {

	c := colly.NewCollector(
		colly.AllowedDomains("arete.com.py", "www.arete.com.py"),
	)

	var total_pages []int

	c.OnHTML("ul.page-numbers", func(e *colly.HTMLElement) {
		selection := e.DOM
		selection.Find("a.page-numbers").Each(func(i int, s *goquery.Selection) {
			page, _ := strconv.Atoi(s.Text())
			total_pages = append(total_pages, page)
		})

	})

	c.OnRequest(func(r *colly.Request) {
		fmt.Printf("Visiting: %s\n", r.URL)
	})

	c.OnError(func(_ *colly.Response, err error) {
		fmt.Printf("Something went wrong: %v \n", err)
	})

	c.Visit("https://arete.com.py/productos.1000")

	// return the max value of the slice
	return total_pages[len(total_pages)-1]
}

func Get_all_products_arete() {
	// var list_of_items []Item

	channels := make([]chan []Item, 0)

	var items_wg sync.WaitGroup

	maxGoRoutines := 10

	guard := make(chan struct{}, maxGoRoutines)

	page_count := Get_total_number_of_pages_arete()

	for i := 1; i < page_count+1; i++ {

		guard <- struct{}{}

		items_wg.Add(1)
		// add a sleep for a eighth of a second
		time.Sleep(125 * time.Millisecond)
		channel := make(chan []Item)

		go func(acc int) {
			items := Get_from_arete(acc)
			defer items_wg.Done()
			<-guard
			channel <- items
		}(i)

		channels = append(channels, channel)

	}

	res := []Item{}

	for _, channel := range channels {
		res = append(res, <-channel...)
	}

	Write_data(res, "arete")

	println("Done!")

	items_wg.Wait()
}
