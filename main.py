import json
import time
import threading
import os
from account_handler import handle_account, update_balance, get_token_for_account
from printer import print_info, print_success, print_error

# Check if the upgrades_response.json file exists, and create it if it doesn't
file_path = 'upgrades_response.json'
if not os.path.exists(file_path):
    with open(file_path, 'w') as file:
        pass  # Create the file without content

# Read headers from JSON file
with open('headers.json', 'r') as headers_file:
    headers = json.load(headers_file)

# Read upgrade IDs from a text file
with open('upgrade_ids.txt', 'r') as file:
    upgrade_ids = [line.strip() for line in file.readlines() if line.strip()]

# Automatic execution for each account
if __name__ == "__main__":
    while True:
        with open('init_data.txt', 'r') as file:
            init_data_list = file.readlines()

        threads = []
        for init_data_raw in init_data_list:
            init_data_raw = init_data_raw.strip()
            if init_data_raw:
                thread = threading.Thread(target=handle_account, args=(init_data_raw, headers, upgrade_ids))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

        # Update balance every 3 seconds during the wait period
        print_info("Please wait 3 seconds before updating the balance...")
        time.sleep(3)

        # Pass both token and headers to update_balance
        for init_data_raw in init_data_list:
            init_data_raw = init_data_raw.strip()
            if init_data_raw:
                token = get_token_for_account(init_data_raw, headers)
                if token:
                    thread = threading.Thread(target=update_balance, args=(token, headers))
                    thread.start()

        print_info("Please wait for 1 hour...")
        time.sleep(3600)
