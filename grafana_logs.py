from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
import pandas as pd
import logging
import json
import os
import sys
from datetime import datetime
import argparse
import time
import pickle

load_dotenv()

# Secrets procted by asgard
GRAFANA_USERNAME = os.getenv("GRAFANA_USERNAME")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD")
COOKIES_FILE = "/home/chandan/Desktop/scripts/cookies.pkl"

EXCEL_DIR = "/home/chandan/Desktop/scripts/error_insights"
if not os.path.exists(EXCEL_DIR):
    os.makedirs(EXCEL_DIR)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")  # Enable DevTools protocol

    # chrome_options.add_argument("--headless")  
   
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def save_cookies(driver, cookies_file):
    """Save cookies to a file."""
    with open(cookies_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies saved.")

def load_cookies(driver, cookies_file, url):
    """Load cookies from a file."""
    driver.get(url)
    if os.path.exists(cookies_file):
        with open(cookies_file, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("Cookies loaded.")
    else:
        print(f"No cookies file found at {cookies_file}. A new session will be created.")


def load_json(file_name):
    try:
        with open(file_name, "r") as file:
            data = json.load(file)
            print(f"Loaded data from {file_name}.")
            return data
    except FileNotFoundError:
        print(f"File '{file_name}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {file_name}: {e}")
        return None


def generate_dynamic_url(domain, time_range, panel):
    base_url = (
        "https://grafana-apj.trafficpeak.live/d/be2way1ysetc0d/error-insights?orgId=431"
    )
    final_url = f"{base_url}&var-AND_reqHost=IN&var-reqHost={domain}&viewPanel={panel}&from=now-{time_range}&to=now"
    print(f"Generated URL: {final_url}")
    return final_url


def finalurl_v2(base_url):
    if "&inspect=5" not in base_url:
        base_url += "&inspect=5"
        print(f"Modified URL: {base_url}")
    else:
        print(f"URL already contains '&inspect=5': {base_url}")
    return base_url


def manual_mode():
    hostname_data = load_json("/home/chandan/Desktop/scripts/data/hostnames.json")
    if not hostname_data:
        return None

    domains = hostname_data.get("domain_specific_hostnames", {})
    if not domains:
        print("No domain groups found in hostname.json.")
        return None

    print("Available domain groups:")
    for index, group in enumerate(domains.keys(), start=1):
        print(f"{index}. {group}")

    try:
        domain_index = int(input("Select a domain group (number): ")) - 1
        if domain_index < 0 or domain_index >= len(domains):
            print("Invalid domain group selection.")
            return None
        domain_key = list(domains.keys())[domain_index]
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None

    subdomains = domains[domain_key]
    print(f"Available subdomains for '{domain_key}':")
    for index, subdomain in enumerate(subdomains, start=1):
        print(f"{index}. {subdomain}")

    try:
        subdomain_index = int(input("Select a subdomain (number): ")) - 1
        if subdomain_index < 0 or subdomain_index >= len(subdomains):
            print("Invalid subdomain selection.")
            return None
        selected_domain = subdomains[subdomain_index]
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None

    time_range = input("Enter time range (e.g., 5m, 6h, 2d): ").strip()
    panel_input = input("Enter panel number (e.g., 1, 2, 3, 4, or 'all'): ").strip()
    max_rows = input("Enter max rows: ").strip()

    return {"domain": selected_domain, "time_range": time_range, "panel": "all" if panel_input.lower() == "all" else int(panel_input), "max_rows": int(max_rows)}



def cron_job_mode():
    config_data = load_json("/home/chandan/Desktop/scripts/configs/config.json")
    if not config_data:
        return None

    cron_params = config_data.get("cron_job_params", {})
    return {
        "domain": cron_params.get("selected_domain", "www.wisden.com"),
        "time_range": cron_params.get("time_range", "6h"),
        "panel": cron_params.get("panel", "all"),
        "max_rows": cron_params.get("max_rows", 10)
        
    }

def login_to_grafana(driver, url, cookies_file):
    """Login to Grafana, using saved cookies if available, else perform login."""
    
    load_cookies(driver, cookies_file, url)
    driver.get(url)
    
    print("Current URL:", driver.current_url)

    
    wait = WebDriverWait(driver, 10)
    
    if "login" in driver.current_url:
        try:
            print("Logging into Grafana...")
            wait.until(EC.presence_of_element_located((By.NAME, "user")))
            username_field = driver.find_element(By.NAME, "user")
            password_field = driver.find_element(By.NAME, "password")
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            
            # Send login credentials
            username_field.send_keys(GRAFANA_USERNAME)
            password_field.send_keys(GRAFANA_PASSWORD)
            login_button.click()
            
            # Wait until login is complete and the dashboard loads
            wait.until(lambda d: "login" not in d.current_url)
            print("Login successful!")
            
            # Save cookies after successful login
            save_cookies(driver, cookies_file)
        except Exception as e:
            print(f"Error during login: {e}")
            logging.error(f"Error during login: {e}")
            sys.exit(1)
    else:
        print("Already logged in using existing session.")      

def zoom_out_dev_tools(driver, zoom_level=0.25):
    dev_tools = driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 2256,
        "height": 5000,
        "deviceScaleFactor": zoom_level,
        "mobile": False
    })
    print(f"Zoom level set to {zoom_level * 100}% using DevTools Protocol.")

def fetch_table_data(driver, max_rows):
    print("Fetching table data...")
    wait = WebDriverWait(driver,2)

    try:
        no_data_message = None
        try:
            no_data_message = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "css-18o2w4z"))
            )
            if no_data_message.text == "No data":
                print("No data available for the selected time range.")
                return None, None  
        except TimeoutException:
            pass

        table_title = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "css-1ej1m3x-panel-title"))
        )
        title = table_title.text
        print(f"Table title: {title}")

        table_header = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "css-1kfgvg7-thead"))
        )
        header_elements = table_header.find_elements(
            By.CSS_SELECTOR, "div[role='columnheader']"
        )
        headers = [
            header.find_element(By.TAG_NAME, "div").text for header in header_elements
        ]

        table_body = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='table']"))
        )
        rows = table_body.find_elements(By.CLASS_NAME, "css-1e8ylo6-row")
        all_rows = []

        print(f"Number of rows visible in the table: {len(rows)}")
        for row in rows[:max_rows]:
            cells = row.find_elements(By.CSS_SELECTOR, "div[role='cell']")
            row_data = [cell.text for cell in cells]
            all_rows.append(row_data)

        df = pd.DataFrame(all_rows[:max_rows], columns=headers)
        print(f"Table data fetched successfully and processed with {max_rows} rows.")
        return title, df

    except TimeoutException as e:
        print(f"Timeout while fetching table data: {e}")
        logging.error(f"Timeout while fetching table data: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error while fetching table data: {e}")
        logging.error(f"Unexpected error while fetching table data: {e}")
        return None, None


logging.basicConfig(
    filename="/home/chandan/Desktop/scripts/logs/grafana_data_fetch.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_folder_name_for_domain(domain, hostname_data):
    domain_groups = hostname_data.get("domain_specific_hostnames", {})
    for group_key, domains in domain_groups.items():
        if domain in domains:
            return group_key
    return "others"

def main():
    parser = argparse.ArgumentParser(description="Grafana Data Fetching Script")
    parser.add_argument(
        "--mode", choices=["manual", "cron"], default="manual",
        help="Select the mode: 'manual' for interactive mode or 'cron' for automated mode"
    )
    args = parser.parse_args()

    if args.mode == "cron":
        params = cron_job_mode()
    else:
        params = manual_mode()

    if not params:
        print("Invalid or missing parameters.")
        logging.error("Invalid or missing parameters.")
        return

    driver = setup_driver()
    zoom_out_dev_tools(driver, zoom_level=0.25)
    
    # Load hostname data
    hostname_data = load_json("/home/chandan/Desktop/scripts/data/hostnames.json")
    if not hostname_data:
        print("Error: Failed to load hostname data.")
        logging.error("Failed to load hostname data.")
        return

    try:
        folder_name = get_folder_name_for_domain(params["domain"], hostname_data)
        hostname_specific_folder = os.path.join(EXCEL_DIR, folder_name)
        if not os.path.exists(hostname_specific_folder):
            os.makedirs(hostname_specific_folder)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        final_folder = os.path.join(hostname_specific_folder, timestamp)
            
        if not os.path.exists(final_folder):
            os.makedirs(final_folder)
        
        if params["panel"] == "all":
            panel_numbers = range(1, 6) 
        else:
            panel_numbers = [params["panel"]]

        url = generate_dynamic_url(params["domain"], params["time_range"], panel_numbers[0])
        # inspect_url = finalurl_v2(url)
        
        login_to_grafana(driver, url, COOKIES_FILE)
        
        max_rows = params["max_rows"]

        for panel in panel_numbers:
            if panel != panel_numbers[0]: 
                url = generate_dynamic_url(params["domain"], params["time_range"], panel)
                # inspect_url = finalurl_v2(url)
                driver.get(url)  
                
            title, df = fetch_table_data(driver, max_rows)
            
            if df is None or df.empty:
                    print(f"No data available for Panel {panel}. Skipping...")
                    logging.info(f"No data available for Panel {panel}. Skipping...")
                    continue
            
            
            
            filename = os.path.join(
                final_folder,
                f"{title.replace(' ', '_')}_{params['domain']}_{params['time_range']}_Panel_{panel}_{timestamp}.xlsx"
                if title
                else f"grafana_unnamed_panel_{params['domain']}_{params['time_range']}_{panel}_{timestamp}.xlsx"
            )

            df.to_excel(filename, index=False)
            print(f"Table data for Panel {panel} saved to '{filename}'.")
            logging.info(f"Table data for Panel {panel} saved to '{filename}'.")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
    finally:
        driver.quit()
if __name__ == "__main__":
    main()

