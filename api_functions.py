"""
API functions for fetching real estate listing data from various sources.
"""
import requests
import pandas as pd


class RealEstateAPI:
    """Handles API calls to various real estate data providers."""

    def __init__(self, scrapeak_key=None, rapidapi_key=None):
        self.scrapeak_key = scrapeak_key or 'c99d5365-e52d-4591-8805-5529e2cc28f9'
        self.rapidapi_key = rapidapi_key or '8c4d33ab1fmsh042342b8342f6f9p1a302djsnf9ae6918b4b9'

    def get_zillow_listings(self, listing_url):
        """
        Fetch Zillow listings using Scrapeak API.

        Args:
            listing_url: Zillow search URL

        Returns:
            DataFrame with listing data
        """
        url = "https://app.scrapeak.com/v1/scrapers/zillow/listing"

        querystring = {
            "api_key": self.scrapeak_key,
            "url": listing_url
        }

        try:
            response = requests.get(url, params=querystring)
            response.raise_for_status()
            data = response.json()
            df = pd.json_normalize(data["data"]["cat1"]["searchResults"]["mapResults"])
            return df
        except Exception as e:
            print(f"Error fetching Zillow listings: {e}")
            return pd.DataFrame()

    def get_zillow_by_working_api(self, listing_url, page_number=1):
        """
        Fetch Zillow listings using Working API (alternative method).

        Args:
            listing_url: Zillow search URL
            page_number: Page number for pagination

        Returns:
            DataFrame with listing data
        """
        url = "https://zillow-working-api.p.rapidapi.com/search/byurl"

        querystring = {
            "url": listing_url,
            "page": page_number
        }

        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "zillow-working-api.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            df = pd.json_normalize(response.json()['Results'])
            return df
        except Exception as e:
            print(f"Error fetching Zillow listings (Working API): {e}")
            return pd.DataFrame()

    def get_redfin_listings(self, listing_url):
        """
        Fetch Redfin listings.

        Args:
            listing_url: Redfin search URL

        Returns:
            DataFrame with listing data
        """
        url = "https://redfin-com-data.p.rapidapi.com/property/search-url"

        querystring = {"url": listing_url}

        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "redfin-com-data.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json()

            # Handle different response structures
            if 'homes' in data.get('data', {}):
                df = pd.json_normalize(data['data']['homes'])
            else:
                # Look for GIS data
                for key in data.get('data', {}).keys():
                    if key.startswith('gis?a') and 'homes' in data['data'][key]:
                        df = pd.json_normalize(data['data'][key]['homes'])
                        break
                else:
                    df = pd.DataFrame()

            return df
        except Exception as e:
            print(f"Error fetching Redfin listings: {e}")
            return pd.DataFrame()

    def get_property_detail(self, zpid):
        """
        Get detailed property information by Zillow Property ID.

        Args:
            zpid: Zillow Property ID

        Returns:
            Response object with property details
        """
        url = "https://app.scrapeak.com/v1/scrapers/zillow/property"

        querystring = {
            "api_key": self.scrapeak_key,
            "zpid": zpid
        }

        return requests.get(url, params=querystring)

    def get_zpid_by_address(self, street, city, state, zip_code=None):
        """
        Get Zillow Property ID by address.

        Args:
            street: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP code (optional)

        Returns:
            Response object with ZPID
        """
        url = "https://app.scrapeak.com/v1/scrapers/zillow/zpidByAddress"

        querystring = {
            "api_key": self.scrapeak_key,
            "street": street,
            "city": city,
            "state": state,
            "zip_code": zip_code
        }

        return requests.get(url, params=querystring)


# Predefined Zillow URLs for Fresno, CA zip codes
FRESNO_ZILLOW_URLS = {
    '93722': 'https://zillow.com/fresno-ca-93722/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A36.871937850818554%2C%22south%22%3A36.73283815503686%2C%22east%22%3A-119.78077706005858%2C%22west%22%3A-119.9902039399414%7D%2C%22usersSearchTerm%22%3A%228153%20N%20Cedar%20Ave%20%23129%20Fresno%2C%20CA%2093720%22%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A12%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A97431%2C%22regionType%22%3A7%7D%5D%2C%22pagination%22%3A%7B%7D%7D',
    '93720': 'https://www.zillow.com/fresno-ca-93720/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A36.89889711124698%2C%22south%22%3A36.829403367399564%2C%22east%22%3A-119.71074728002928%2C%22west%22%3A-119.81546071997069%7D%2C%22usersSearchTerm%22%3A%228153%20N%20Cedar%20Ave%20%23129%20Fresno%2C%20CA%2093720%22%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A13%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A97429%2C%22regionType%22%3A7%7D%5D%2C%22pagination%22%3A%7B%7D%7D',
    '93705': 'https://www.zillow.com/fresno-ca-93705/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A36.82125687406157%2C%22south%22%3A36.75169254968076%2C%22east%22%3A-119.7745407800293%2C%22west%22%3A-119.8792542199707%7D%2C%22usersSearchTerm%22%3A%228153%20N%20Cedar%20Ave%20%23129%20Fresno%2C%20CA%2093720%22%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A13%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A97416%2C%22regionType%22%3A7%7D%5D%2C%22pagination%22%3A%7B%7D%7D',
    '93711': 'https://www.zillow.com/fresno-ca-93711/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A36.907976289605614%2C%22south%22%3A36.76894213918674%2C%22east%22%3A-119.7256510600586%2C%22west%22%3A-119.93507793994141%7D%2C%22usersSearchTerm%22%3A%228153%20N%20Cedar%20Ave%20%23129%20Fresno%2C%20CA%2093720%22%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A12%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A97422%2C%22regionType%22%3A7%7D%5D%2C%22pagination%22%3A%7B%7D%7D',
    '93710': 'https://www.zillow.com/fresno-ca-93710/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A36.85422044243024%2C%22south%22%3A36.784686068675306%2C%22east%22%3A-119.7099347800293%2C%22west%22%3A-119.8146482199707%7D%2C%22usersSearchTerm%22%3A%228153%20N%20Cedar%20Ave%20%23129%20Fresno%2C%20CA%2093720%22%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A13%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A97421%2C%22regionType%22%3A7%7D%5D%2C%22pagination%22%3A%7B%7D%7D',
    '93728': 'https://www.zillow.com/fresno-ca-93728/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A36.7908501819575%2C%22south%22%3A36.72125825056633%2C%22east%22%3A-119.76504978002929%2C%22west%22%3A-119.8697632199707%7D%2C%22usersSearchTerm%22%3A%228153%20N%20Cedar%20Ave%20%23129%20Fresno%2C%20CA%2093720%22%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A13%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A97436%2C%22regionType%22%3A7%7D%5D%2C%22pagination%22%3A%7B%7D%7D',
    '93726': 'https://www.zillow.com/fresno-ca-93726/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A36.82770809522596%2C%22south%22%3A36.7581496305962%2C%22east%22%3A-119.70796928002929%2C%22west%22%3A-119.8126827199707%7D%2C%22usersSearchTerm%22%3A%228153%20N%20Cedar%20Ave%20%23129%20Fresno%2C%20CA%2093720%22%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%2C%22tow%22%3A%7B%22value%22%3Afalse%7D%2C%22con%22%3A%7B%22value%22%3Afalse%7D%2C%22apco%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22manu%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A13%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A97434%2C%22regionType%22%3A7%7D%5D%2C%22pagination%22%3A%7B%7D%7D',
}
