# Grafana Scrapper  

## Introduction  
This script helps in extracting and organizing logs from Grafana dashboards. It supports both manual and automated execution modes, making it flexible for various use cases.

---

## Configuration  

1. **Environment Variables:**  
   - Create a `.env` file to store your credentials.  
   - Refer to the `grafana_logs.py` file for required variables.

2. **Hostnames:**  
   - To update the available hostnames, run:  
     ```bash
     python3 get_hostname.py
     ```  
   - This will generate a `hostnames.json` file in the `data` folder (useful for manual mode).

3. **Modes of Execution:**  
   There are two modes available:
   - **Manual Mode:**  
     ```bash
     python3 grafana_logs.py --mode manual
     ```  
     - Provides an interactive menu to choose options.
   - **Cron Job Mode:**  
     ```bash
     python3 grafana_logs.py --mode cron
     ```  
     - Configure the following in `configs/configs.json`:  
       - Hostname  
       - Panel number  
       - Time range  
       - Number of rows to fetch  

---

## Output  

After successful execution:  
- A folder is created to store the processed data in the following structure:  

- **Execution Logs:**  
- For manual execution:  
  Logs will be saved in `logs/grafana_data_fetch.log`.  
- For cron job execution:  
  Logs will be saved in `cron_job.logs`.

---

## Key Files and Folders  

- **Scripts:**  
- `grafana_logs.py`: Main script to execute in manual or cron mode.  
- `get_hostname.py`: Updates the hostnames list.  

- **Configuration Files:**  
- `.env`: Stores credentials.  
- `configs/configs.json`: Stores settings for cron job execution.  

- **Output Directory:**  
- `error_insights/`: Contains the processed Excel files.  

- **Data Directory:**  
- `data/hostnames.json`: Stores updated hostnames.

---
