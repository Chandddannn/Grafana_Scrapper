# Grafana_Scrapper

add a .env file with you credentials by refering the grafan_logs.py 

If you want to update the avalable hostname run the get_hostname.py file which will save the hostnames.json in data folder (useful for manual mode) 

There are two modes : Manual & Cron 

Manual execution: python3 grafana_logs.py --mode manual

Cron_Job execution: python3 grafana_logs.py --mode cron

if you are running manual you will have a interactive menu to choose from the options.

if running cron job you change change the hostname, panel number , timerange and no of rows to be fetched in the configs/configs.json






