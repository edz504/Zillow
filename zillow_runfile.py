# -*- coding: utf-8 -*-
'''
WARNING: Use this code at your own risk, scraping is against Zillow's TOC.

Zillow home listings scraper, using Selenium.  The code takes as input search 
terms that would normally be entered on the Zillow home page.  It creates 11 
variables on each home listing from the data, saves them to a data frame, 
and then writes the df to a CSV file that gets saved to your working directory.

Software requirements/info:
- This code was written using Python 3.5.
- Scraping is done with Selenium v3.0.2, which can be downloaded here: 
  http://www.seleniumhq.org/download/
- The selenium package requires a webdriver program. This code was written 
  using Chromedriver v2.25, which can be downloaded here: 
  https://sites.google.com/a/chromium.org/chromedriver/downloads
  
'''

import time
import pandas as pd
import zillow_functions as zl
from bs4 import BeautifulSoup

# Create list of search terms.
# Function zipcodes_list() creates a list of US zip codes that will be 
# passed to the scraper. For example, st = zipcodes_list(['10', '11', '606'])  
# will yield every US zip code that begins with '10', begins with "11", or 
# begins with "606" as a single list.
# I recommend using zip codes, as they seem to be the best option for catching
# as many house listings as possible. If you want to use search terms other 
# than zip codes, simply skip running zipcodes_list() function below, and add 
# a line of code to manually assign values to object st, for example:
# st = ['Chicago', 'New Haven, CT', '77005', 'Jacksonville, FL']
# Keep in mind that, for each search term, the number of listings scraped is 
# capped at 520, so in using a search term like "Chicago" the scraper would 
# end up missing most of the results.
# Param st_items can be either a list of zipcode strings, or a single zipcode 
# string.
st = zl.zipcodes_list(st_items = ["94065", # Bair Island
                                  "94070", # San Carlos
                                  "94063", # RWC1
                                  "94062", # Emerald Hills
                                  "94061", # RWC2
                                  "94027", # Atherton
                                  "94025", # Menlo Park
                                  "94301", # PA1
                                  "94305", # Stanford
                                  "94306", # PA2
                                  "94304", # PA Hills
                                  "94022", # Los Altos 1
                                  "94028", # Portola Valley,
                                  "94043", # MTV1
                                  "94041", # MTV2
                                  "94040", # MTV3
                                  "94024"  # Los Altos 2
                                  ])

NUM_BEDS = 3

# Initialize the webdriver.
driver = zl.init_driver("/Users/edz/Documents/Projects/zillow/chromedriver")

# Go to www.zillow.com/homes/for_rent/
zl.navigate_to_website(driver, "http://www.zillow.com/homes/for_rent")

# These variables will make up the final output dataframe.
df = pd.DataFrame(columns=['address', 'city', 'type', 'price', 'bedrooms',
                           'bathrooms','sqft', 'days_on_zillow', 'url',
                           'zip'])

# Get total number of search terms.
numSearchTerms = len(st)

# Start the scraping.
for k in range(numSearchTerms):
    # Define search term (must be str object).
    search_term = st[k]

    # Enter search term, filter, and execute search.
    if zl.enter_search_term(driver, search_term):
        print("Entering search term number " + str(k+1) + 
              " out of " + str(numSearchTerms))
    else:
        print("Entering search term " + str(k+1) + 
              " failed, moving onto next search term\n***")
        continue

    # Use this as a filter ahead of time, so that for the apartment complexes
    # with non-standard card formatting, we can just pick the first
    # (it comes in the form 2 <bed icon> $X+, 3 <bed icon> $Y+).
    if zl.select_num_bed_filter(driver, NUM_BEDS):
        print("Entering number of bedrooms filter ({})".format(3))
    else:
        print("Entering number of bedrooms at search term " + str(k+1) + 
              " failed, moving onto next search term\n***")
        continue

    if zl.search(driver):
      print("Actually searching...")
    else:
      print("Couldn't actually search :(")
    
    # Check to see if any results were returned from the search.
    # If there were none, move onto the next search.
    if zl.results_test(driver):
        print("Search " + str(search_term) + 
              " returned zero results. Moving onto the next search\n***")
        continue
    
    # Pull the html for each page of search results. Zillow caps results at 
    # 20 pages, each page can contain 26 home listings, thus the cap on home 
    # listings per search is 520.
    rawdata = zl.get_html(driver)
    print(str(len(rawdata)) + " pages of listings found")
    
    # Take the extracted HTML and split it up by individual home listings.
    listings = zl.get_listings(rawdata)
    
    # For each home listing, extract the variables that will populate that 
    # specific observation within the output dataframe.
    for n in range(len(listings)):
        soup = BeautifulSoup(listings[n], "lxml")

        if zl.is_apartment_complex(soup, NUM_BEDS):
          print("Found apartment complex...")
          new_obs = zl.create_obs_from_apartment_complex(soup, NUM_BEDS,
                                                         search_term)
        else:
          new_obs = zl.create_obs_from_standard(soup, NUM_BEDS)
    
        # Append new_obs to df as a new observation
        if new_obs is not None and len(new_obs) == len(df.columns):
            df.loc[len(df.index)] = new_obs

# Close the webdriver connection.
zl.close_connection(driver)

# Write df to CSV.
dt = time.strftime("%Y-%m-%d") + "_" + time.strftime("%H%M%S")
filename = str(dt) + ".csv"
df.to_csv(filename, index=False, encoding='utf-8')
