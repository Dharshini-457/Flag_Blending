from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import datetime
import time
import re

CHROME_DRIVER_PATH = "C://Users//dhars//Downloads//chromedriver-win64//chromedriver-win64//chromedriver.exe"
BASE_URL = "https://sourcing.alibaba.com/rfq/rfq_search_list.htm?country=AE&recently=Y&tracelog=newest"
DEBUG_MODE = True

options = webdriver.ChromeOptions()
if not DEBUG_MODE:
    options.add_argument("--headless")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
wait = WebDriverWait(driver, 25)
driver.get(BASE_URL)

# === Accept cookie popup ===
try:
    accept_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.ID, "compliance_popup_accept"))
    )
    accept_btn.click()
except:
    pass

rfq_data = []

# === Pagination loop ===
while True:
    time.sleep(3)
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "brh-rfq-item")))
    rfq_cards = driver.find_elements(By.CLASS_NAME, "brh-rfq-item")
    print(f"🛒 Found {len(rfq_cards)} RFQs on this page.")

    for idx, card in enumerate(rfq_cards):
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, ".brh-rfq-item__subject-link")
            title = title_elem.text.strip()
            inquiry_url = title_elem.get_attribute("href")
            inquiry_time = card.find_element(By.CSS_SELECTOR, ".brh-rfq-item__publishtime").text.strip()
            country = card.find_element(By.CSS_SELECTOR, ".brh-rfq-item__country").text.strip()
            quotes_left = card.find_element(By.CSS_SELECTOR, ".brh-rfq-item__quote-left span").text.strip()

            # Extract RFQ ID from URL
            rfq_id = "N/A"
            match = re.search(r'(\d{8,})', inquiry_url)
            if match:
                rfq_id = match.group(1)

            scraping_date = datetime.datetime.now().strftime("%Y-%m-%d")

            # === Open detail page in new tab ===
            try:
                driver.execute_script("window.open('');")
                time.sleep(1)
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(inquiry_url)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".username")))

                def try_find(selector):
                    try:
                        return driver.find_element(By.CSS_SELECTOR, selector).text.strip()
                    except:
                        return "N/A"

                def has_element(selector):
                    return "Yes" if driver.find_elements(By.CSS_SELECTOR, selector) else "No"

                buyer_name = try_find(".username")
                buyer_img = driver.find_element(By.CSS_SELECTOR, ".user-img img").get_attribute("src") if driver.find_elements(By.CSS_SELECTOR, ".user-img img") else "N/A"
                quantity_required = try_find(".quantity .value")
                email_confirmed = has_element(".email-status.ok")
                experienced_buyer = has_element(".experience-label")
                complete_order = "Yes" if "Complete Order via RFQ" in driver.page_source else "No"
                typical_replies = try_find(".reply-count")
                interactive_user = has_element(".activity-badge")
                inquiry_date = try_find(".inquiry-date")

                rfq_data.append({
                    "RFQ ID": rfq_id,
                    "Title": title,
                    "Buyer Name": buyer_name,
                    "Buyer Image": buyer_img,
                    "Inquiry Time": inquiry_time,
                    "Quotes Left": quotes_left,
                    "Country": country,
                    "Quantity Required": quantity_required,
                    "Email Confirmed": email_confirmed,
                    "Experienced Buyer": experienced_buyer,
                    "Complete Order via RFQ": complete_order,
                    "Typical Replies": typical_replies,
                    "Interactive User": interactive_user,
                    "Inquiry URL": inquiry_url,
                    "Inquiry Date": inquiry_date,
                    "Scraping Date": scraping_date
                })

                print(f"✅ Scraped: {title} [{rfq_id}]")

            except Exception as detail_err:
                print(f"⚠️ Failed to load detail page: {detail_err}")

            finally:
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except Exception as ex:
                    print(f"❌ Failed to close tab or switch back: {ex}")
                    driver.quit()
                    exit()

        except Exception as e:
            print(f"⚠️ Error on RFQ card: {e}")
            continue

    # === Handle pagination ===
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "li.pagination-next")
        if "disabled" in next_btn.get_attribute("class"):
            print("✅ Reached last page.")
            break
        else:
            print("➡️ Going to next page...")
            next_btn.click()
            time.sleep(2)
    except:
        print("❌ No next page button found. Stopping.")
        break

# === Save to CSV ===
if rfq_data:
    df = pd.DataFrame(rfq_data)
    df.to_csv("alibaba_rfq_data_full.csv", index=False, encoding="utf-8-sig")
    print("✅ Saved: alibaba_rfq_data_full.csv")
else:
    print("⚠️ No data collected.")

driver.quit()
print("✅ Scraping completed successfully.")
exit(0)