package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("Starting scraper...")
	start := time.Now()

	// companies.Get_all_products_stock()
	// companies.Get_all_products_superseis()

	// companies.Get_all_products_casarica_con()
	// companies.Get_all_products_arete()

	elapsed := time.Since(start)
	fmt.Printf("Time elapsed: %s\n", elapsed)

}
