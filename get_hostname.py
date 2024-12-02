import json
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from grafana_logs import login_to_grafana, setup_driver
from dotenv import load_dotenv

load_dotenv()

def extract_hostnames(driver, url):
    driver.get(url)
    print("Navigating to URL:", url)

    wait = WebDriverWait(driver, 10)
    dropdown_button = wait.until(EC.element_to_be_clickable((By.ID, "var-reqHost")))
    
    dropdown_button.click()
    print("Dropdown button clicked.")
    
    dropdown_ul = wait.until(EC.presence_of_element_located((By.ID, "options-reqHost")))
    
    li_elements = dropdown_ul.find_elements(By.TAG_NAME, "li")
    
    all_hostnames = []
    
    for li in li_elements:
        try:
            hostname = li.text.strip() 
            if hostname:  
                all_hostnames.append(hostname)
                print(f"Extracted hostname: {hostname}")  
        except Exception as e:
            print(f"Error extracting hostname from li element: {e}")
    
    return all_hostnames

def group_hostnames_by_domain(all_hostnames, shortnames):
    domain_specific_hostnames = {key: [] for key in shortnames}

    domain_specific_hostnames['others'] = []

    for hostname in all_hostnames:
        matched = False
        
        for shortname, domains in shortnames.items():
            for domain in domains:
                try:
                    pattern = f".*{re.escape(domain)}.*"
                    if re.search(pattern, hostname, re.IGNORECASE):
                        domain_specific_hostnames[shortname].append(hostname)
                        matched = True
                        break
                except re.error as e:
                    print(f"Regex error for domain '{domain}': {e}")
            
            if matched:
                break
        
        if not matched:
            domain_specific_hostnames['others'].append(hostname)

    return domain_specific_hostnames

def save_all_data_to_json(all_hostnames, shortnames, domain_specific_hostnames, filename='data/hostnames.json'):
    data = {
        'all_hostnames': all_hostnames, 
        'domain_specific_hostnames': domain_specific_hostnames
    }

    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    
    print(f"Data has been saved to '{filename}'.")

def main():
    driver = setup_driver()

    try:
        hostname_url = "https://grafana-apj.trafficpeak.live/d/be2way1ysetc0d/error-insights?orgId=431"

        print("Logging into Grafana...")
        login_to_grafana(driver, hostname_url)

        all_hostnames = extract_hostnames(driver, hostname_url)

        shortnames = {
            "wis": ["wisden"],
            "mi": ["mumbaiindians"],
            "gt": ["gujarattititans", "gujarat-titans", "gujarattitansipl", "gt"],
            "kkr": ["kkr"],
            "dc": ["delhicapitals", "dc"],
            "kxip": ["punjabkings", "punjab-kings"],
            "lsg": ["lucknowsupergiants", "sg", "lsg"],
            "rr": ["rajasthanroyals"],
            "isl": ["indiansuperleague", "isl"],
            "fih": ["fih"],
            "paralympic": ["paralympic"],
            "ecn": ["ecn"],
            "kc": ["knightclub", "kc"]
        }

        domain_specific_hostnames = group_hostnames_by_domain(all_hostnames, shortnames)

        save_all_data_to_json(all_hostnames, shortnames, domain_specific_hostnames)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
