from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

def extract_book_id(book_url):
    try:
        return book_url.split("/book/")[1].split("/")[0]
    except:
        return None

def push_to_google_sheets(data):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("AllAuthor Books").sheet1
    sheet.clear()
    sheet.append_row([
        "Book ID", "Book Title", "Book Link", "Author Name", "Author Link", "Author Website",
        "Facebook", "Twitter", "Instagram", "Goodreads", "Amazon",
        "YouTube", "Pinterest", "Linkedin", "Join Author's Newsletter"
    ])

    for book in data:
        sheet.append_row([
            book["book_id"], book["book_title"], book["book_link"],
            book["author_name"], book["author_link"], book["author_website"],
            book.get("Facebook", ""), book.get("Twitter", ""), book.get("Instagram", ""),
            book.get("Goodreads", ""), book.get("Amazon", ""), book.get("YouTube", ""),
            book.get("Pinterest", ""), book.get("Linkedin", ""), book.get("Join Author's Newsletter", "")
        ])

def scrape_first_5_books():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://allauthor.com/books/")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.odd, tr.even"))
    )

    books = driver.find_elements(By.CSS_SELECTOR, "tr.odd, tr.even")
    print(f"🧐 Found {len(books)} book rows on page")

    results = []

    for book in books[:5]:
        try:
            book_link = book.find_element(By.CSS_SELECTOR, ".bookname a").get_attribute("href")
            book_title = book.find_element(By.CSS_SELECTOR, ".bookname a").text.strip()
            author_name = book.find_element(By.CSS_SELECTOR, ".book-author-name a").text.strip()
            author_link = book.find_element(By.CSS_SELECTOR, ".book-author-name a").get_attribute("href")
            book_id = extract_book_id(book_link)

            print(f"📘 {book_title} by {author_name}")

            driver.execute_script("window.open(arguments[0]);", author_link)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(random.uniform(1.5, 3.5))

            try:
                website_link = driver.find_element(By.XPATH, "//a[text()='Website']")
                author_website = website_link.get_attribute("href")
            except:
                author_website = "N/A"

            platforms = [
                "Facebook", "Twitter", "Instagram", "Goodreads", "Amazon",
                "YouTube", "Pinterest", "Linkedin", "Join Author's Newsletter"
            ]
            social_links = {platform: "" for platform in platforms}
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    text = link.text.strip()
                    if text in social_links:
                        social_links[text] = link.get_attribute("href")
                except:
                    continue

            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            results.append({
                "book_id": book_id,
                "book_title": book_title,
                "book_link": book_link,
                "author_name": author_name,
                "author_link": author_link,
                "author_website": author_website,
                **social_links
            })

            time.sleep(random.uniform(1, 2.5))

        except Exception as e:
            print(f"⚠️ Error with one book: {e}")
            continue

    driver.quit()
    push_to_google_sheets(results)
    print(f"✅ Scraped {len(results)} books. Data pushed to Google Sheets!")

if __name__ == "__main__":
    scrape_first_5_books()
