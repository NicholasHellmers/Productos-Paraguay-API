package companies

import (
	"context"
	"log"
	"strings"

	"github.com/chromedp/chromedp"
)

// This script is used to scrape all products from biggie.com.py through a headless browser
// and write the data to a csv file in the output/data folder
// The script is called from main.go
func Test_headless() {
	// create context
	ctx, cancel := chromedp.NewContext(context.Background())
	defer cancel()

	// run task list
	var res string

	err := chromedp.Run(ctx,
		chromedp.Navigate(`https://biggie.com.py/products/alimentos-especiales?skip=0`),
		// chromedp.OuterHTML(`div.row`, &res),
		chromedp.Sleep(5),
		chromedp.InnerHTML(`div.row`, &res),
	)

	if err != nil {
		log.Fatal(err)
	}

	log.Println(strings.TrimSpace(res))
}
