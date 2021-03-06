# -*- coding: utf-8 -*-
# Zillow scraper functions, these are sourced at the top of zillow_runfile.py

import json
import re as re
import time
import zipcode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from bs4 import Comment

def zipcodes_list(st_items):
    # If st_items is a single zipcode string.
    if type(st_items) == str:
        zcObjects = zipcode.islike(st_items)
        output = [str(i).split(" ", 1)[1].split(">")[0] 
                    for i in zcObjects]
    # If st_items is a list of zipcode strings.
    elif type(st_items) == list:
        zcObjects = [n for i in st_items for n in zipcode.islike(str(i))]
        output = [str(i).split(" ", 1)[1].split(">")[0] 
                    for i in zcObjects]
    else:
        raise ValueError("input 'st_items' must be of type str or list")
    return(output)

def init_driver(filepath):
    driver = webdriver.Chrome(executable_path = filepath)
    driver.wait = WebDriverWait(driver, 10)
    return(driver)

def navigate_to_website(driver, site):
    driver.get(site)

def click_buy_button(driver):
    try:
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "nav-header")))
        button.click()
        time.sleep(10)
    except (TimeoutException, NoSuchElementException):
        raise ValueError("Clicking the 'Buy' button failed")

def enter_search_term(driver, search_term):
    try:
        searchBar = driver.wait.until(EC.presence_of_element_located(
            (By.ID, "citystatezip")))
        searchBar.clear()
        time.sleep(3)
        searchBar.send_keys(search_term)
        time.sleep(3)
        return(True)
    except (TimeoutException, NoSuchElementException):
        return(False)

def select_num_bed_filter(driver, num_beds):
    try:
        dropdown = driver.wait.until(EC.element_to_be_clickable(
            (By.ID, "beds-menu-label")))
        dropdown.click()
        time.sleep(3)
        bed_selection = driver.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//ul[@id='bed-options']/li[{}]/a".format(
                num_beds + 1))))
        bed_selection.click()
        time.sleep(3)
        return(True)
    except (TimeoutException, NoSuchElementException):
        return(False)

def search(driver):
    try:
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "zsg-icon-searchglass")))
        button.click()
        time.sleep(3)
        return(True)
    except (TimeoutException, NoSuchElementException):
        return(False)

def results_test(driver):
    # Check to see if there are any returned results
    try:
        no_results = driver.find_element_by_css_selector(
            '.zoom-out-message').is_displayed()
    except (NoSuchElementException, TimeoutException):
        # Check to see if the zipcode is invalid or not
        try:
            no_results = driver.find_element_by_class_name(
                'zsg-icon-x-thick').is_displayed()
        except (NoSuchElementException, TimeoutException):
            no_results = False
    return(no_results)

def get_html(driver):
    output = []
    keep_going = True
    while keep_going:
        # Pull page HTML
        try:
            output.append(driver.page_source)
        except TimeoutException:
            pass
        try:
            # Check to see if a "next page" link exists
            keep_going = driver.find_element_by_class_name(
                'zsg-pagination-next').is_displayed()
        except NoSuchElementException:
            keep_going = False
        if keep_going:
            # Test to ensure the "updating results" image isnt displayed. 
            # Will try up to 5 times before giving up, with a 5 second wait 
            # between each try. 
            tries = 5
            try:
                cover = driver.find_element_by_class_name(
                    'list-loading-message-cover').is_displayed()
            except (TimeoutException, NoSuchElementException):
                cover = False
            while cover and tries > 0:
                time.sleep(5)
                tries -= 1
                try:
                    cover = driver.find_element_by_class_name(
                        'list-loading-message-cover').is_displayed()
                except (TimeoutException, NoSuchElementException):
                    cover = False
            # If the "updating results" image is confirmed to be gone 
            # (cover == False), click next page. Otherwise, give up on trying 
            # to click thru to the next page of house results, and return the 
            # results that have been scraped up to the current page.
            if cover == False:
                try:
                    driver.wait.until(EC.element_to_be_clickable(
                        (By.CLASS_NAME, 'zsg-pagination-next'))).click()
                    time.sleep(3)
                except TimeoutException:
                    keep_going = False
            else:
                keep_going = False
    return(output)

def get_listings(list_obj):
    # Split the raw HTML into segments, one for each listing.
    output = []
    for i in list_obj:
        htmlSplit = i.split('" id="zpid_')[1:]
        output += htmlSplit
    print(str(len(output)) + " home listings scraped\n***")
    return(output)

def get_street_address(soup_obj):
    try:
        street = soup_obj.find(
            "span", {"itemprop" : "streetAddress"}).get_text().strip()
    except (ValueError, AttributeError):
        try:
            street = soup_obj.find(
                "span", {"class" : "zsg-photo-card-address"}).get_text().strip()
        except (ValueError, AttributeError):
            street = "NA"
    if len(street) == 0 or street == "null":
        street = "NA"
    return(street)
    
    
def get_city(soup_obj):
    try:
        city = soup_obj.find(
            "span", {"itemprop" : "addressLocality"}).get_text().strip()
    except (ValueError, AttributeError):
        city = "NA"
    if len(city) == 0 or city == "null":
        city = "NA"
    return(city)

def get_state(soup_obj):
    try:
        state = soup_obj.find(
            "span", {"itemprop" : "addressRegion"}).get_text().strip()
    except (ValueError, AttributeError):
        state = "NA"
    if len(state) == 0 or state == 'null':
        state = "NA"
    return(state)
    
def get_zipcode(soup_obj):
    try:
        zipcode = soup_obj.find(
            "span", {"itemprop" : "postalCode"}).get_text().strip()
    except (ValueError, AttributeError):
        zipcode = "NA"
    if len(zipcode) == 0 or zipcode == 'null':
        zipcode = "NA"
    return(zipcode)

def get_price(soup_obj, list_obj):
    # Look for price within the BeautifulSoup object.
    try:
        price = soup_obj.find(
            "span", {"class" : "zsg-photo-card-price"}).get_text().strip()
    except (ValueError, AttributeError):
        # If that fails, look for price within list_obj (object "card_info").
        try:
            price = [n for n in list_obj 
                if any(["$" in n, "K" in n, "k" in n])]
            if len(price) > 0:
                price = price[0].split(" ")
                price = [n for n in price if re.search("[0-9]", n) is not None]
                if len(price[0]) > 0:
                    price = price[0]
                else:
                    price = "NA"
            else:
                price = "NA"
        except (ValueError, AttributeError):
            price = "NA"
    if len(price) == 0 or price == "null":
        price = "NA"
    if price is not "NA":
        # Transformations to the price string.
        price = price.replace(",", "").replace("$", "").replace("/mo", "").replace("+", "")
        if len(price) == 0:
            price = 'NA'
    return(price)
    
def get_card_info(soup_obj):
    # For most listings, card_info will contain info on number of bedrooms, 
    # number of bathrooms, square footage, and sometimes price.
    try:
        card = soup_obj.find(
            "span", {"class" : "zsg-photo-card-info"}).get_text().split(u' \xb7 ')
    except (ValueError, AttributeError):
        card = "NA"
    if len(card) == 0 or card == 'null':
        card = "NA"
    return(card)

def get_sqft(list_obj):
    sqft = [n for n in list_obj if "sqft" in n]
    if len(sqft) > 0:
        try:
            sqft = float(sqft[0].split("sqft")[0].strip().replace(",", "").replace("+", ""))
        except (ValueError, IndexError):
            sqft = "NA"
        if sqft == 0:
            sqft = "NA"
    else:
        sqft = "NA"
    return(sqft)

def get_bedrooms(list_obj):
    beds = [n for n in list_obj if any(["bd" in n, "tudio" in n])]
    if len(beds) > 0:
        if any([beds[0] == "Studio", beds[0] == "studio"]):
            beds = 0
            return(beds)
        try:
            beds = float(beds[0].split("bd")[0].strip())
        except (ValueError, IndexError):
            if any([beds[0] == "Studio", beds[0] == "studio"]):
                beds = 0
            else:
                beds = "NA"
    else:
        beds = "NA"
    return(beds)

def get_bathrooms(list_obj):
    baths = [n for n in list_obj if "ba" in n]
    if len(baths) > 0:
        try:
            baths = float(baths[0].split("ba")[0].strip())
        except (ValueError, IndexError):
            baths = "NA"
        if baths == 0:
            baths = "NA"
    else:
        baths = "NA"
    return(baths)

def get_days_on_zillow(soup_obj):
    try:
        dom = soup_obj.find_all(
            "span", {"class" : "zsg-photo-card-notification"})
        if len(dom) > 0:
            dom = dom[0].get_text().strip()
            # e.g. "4 hours ago"
            if 'hours ago' in dom:
                dom = round(float(dom.split(" ")[0]) / 24, 3)
            # e.g. "Updated yesterday"
            elif 'yesterday' in dom:
                dom = 0
            else:
                dom = int(dom.split(" ")[0])
        else:
            dom = "NA"
    except (ValueError, AttributeError):
        dom = "NA"
    return(dom)

def get_rental_type(soup_obj):
    try:
        rentaltype = soup_obj.find(
            "span", {"class" : "zsg-photo-card-status"}).get_text().strip()
    except (ValueError, AttributeError):
        rentaltype = "NA"
    if len(rentaltype) == 0 or rentaltype == 'null':
        rentaltype = "NA"
    return(rentaltype)

def get_url(soup_obj):
    # Try to find url in the BeautifulSoup object.
    try:
        link = soup_obj.find(
            "a", {"class": ("zsg-photo-card-overlay-link")})
    except (ValueError, AttributeError):
        return("NA")
    return "http://www.zillow.com" + link.get("href")

def create_obs_from_standard(soup, num_beds):
    new_obs = []
    card_info = get_card_info(soup)
        
    # Street Address
    new_obs.append(get_street_address(soup))

    # City
    new_obs.append(get_city(soup))

    # Type (House, Apartment, Condo, etc.)
    new_obs.append(get_rental_type(soup))
    
    # Price
    new_obs.append(get_price(soup, card_info))

    # Bedrooms (only keep == 3, filter will return 3+)
    num_bedrooms = get_bedrooms(card_info)
    if num_bedrooms != num_beds:
        return None
    new_obs.append(num_bedrooms)

    # Bathrooms (only keep >= 2)
    num_bathrooms = get_bathrooms(card_info)
    if num_bathrooms < 2:
        return None
    new_obs.append(num_bathrooms)
   
    # Sqft
    new_obs.append(get_sqft(card_info))

    # Days on Zillow
    new_obs.append(get_days_on_zillow(soup))
    
    # URL for each house listing
    new_obs.append(get_url(soup))
    
    # Zipcode
    new_obs.append(get_zipcode(soup))

    return new_obs

def is_apartment_complex(soup_obj, num_beds):
    # Apartment complexes have something like 3 <bed-icon> $X+
    # instead of the typical information in their card_info.
    try:
        card = soup_obj.find(
            "span", {"class" : "zsg-photo-card-unit"}).get_text().split("$")
    except (ValueError, AttributeError):
        return False
    # Let's also make sure that the first number of beds is the one we want.
    assert num_beds == int(card[0])
    return True

def get_price_from_apartment_complex_card(list_obj):
    # First element is # beds, second is the associated price.
    return float(list_obj[1].replace(",", "").replace("+", "")) 

def get_mini_bubble_info(soup_obj):
    try:
        minibubble = soup_obj.find(
            "div", {"class" : "minibubble"})
    except (ValueError, AttributeError):
        return "NA"
    # Process into a dictionary for return.
    comments = minibubble.findAll(text=lambda text:isinstance(text, Comment))
    return json.loads(comments[0].replace("<!--", "").replace("-->", ""))

def create_obs_from_apartment_complex(soup, num_beds, zip_code):
    new_obs = []
    try:
        card = soup.find(
            "span", {"class" : "zsg-photo-card-unit"}).get_text().split("$")
    except (ValueError, AttributeError):
        card = "NA"
        
    # Street Address (same as standard)
    address = get_street_address(soup)
    new_obs.append(address)

    # City -- can't retrieve this from HTML, just take the 2nd to last comma
    # split.
    new_obs.append(address.split(", ")[-2])

    # We know this is an apartment complex.
    new_obs.append("Apartment Complex")
    
    # Price
    new_obs.append(get_price_from_apartment_complex_card(card))

    # Bedrooms (must be num_beds)
    new_obs.append(num_beds)

    minibubble = get_mini_bubble_info(soup)

    if minibubble == "NA":
        return None

    # Bathrooms (only keep >= 2)
    num_bathrooms = minibubble["bath"]
    if num_bathrooms < 2:
        return None
    new_obs.append(num_bathrooms)
   
    # Sqft
    new_obs.append(minibubble["sqft"])

    # Days on Zillow
    new_obs.append(get_days_on_zillow(soup))
    
    # URL for each house listing
    new_obs.append(get_url(soup))
    
    # Zipcode
    new_obs.append(zip_code)

    return new_obs

def close_connection(driver):
    driver.quit()
