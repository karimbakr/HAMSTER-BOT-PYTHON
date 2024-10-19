import json
import requests
import re
import time
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Define print functions with colors
def print_success(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def print_info(message):
    print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")

def print_account_info(name, balance_diamonds, upgrade_status):
    print(f"{'Account Name':<20}{'Diamonds Balance':<20}{'Upgrade Status':<20}")
    print(f"{'-'*60}")
    print(f"{name:<20}{balance_diamonds:<20}{upgrade_status:<20}")

def print_upgrade_status_with_number(upgrades):
    print(f"\n{'#':<5}{'Upgrade ID':<25}{'Status':<25}{'Required Funds':<25}{'Cooldown (minutes)':<25}")
    print(f"{'-'*105}")
    for index, upgrade in enumerate(upgrades, start=1):
        upgrade_id = upgrade['id']
        status = upgrade.get('status', '')
        required_funds = upgrade.get('required_funds', 'N/A')
        cooldown_minutes = upgrade.get('cooldown_seconds', 'N/A')
        
        # Print the numbering and details
        if status == 'cooldown':
            print(f"{index:<5}{upgrade_id:<25}{'In Cooldown':<25}{'N/A':<25}{cooldown_minutes/60:<25}")
        elif status == 'max_level':
            print(f"{index:<5}{upgrade_id:<25}{'Max Level':<25}{'N/A':<25}{'N/A':<25}")
        elif status == 'insufficient_funds':
            print(f"{index:<5}{upgrade_id:<25}{'Insufficient Funds':<25}{required_funds:<25}{'N/A':<25}")
        else:
            print(f"{index:<5}{upgrade_id:<25}{'Upgraded':<25}{'N/A':<25}{'N/A':<25}")

def update_balance(token, headers):
    url_sync = "https://api.hamsterkombatgame.io/interlude/sync"
    headers_sync = headers['syncRequest']
    headers_sync['authorization'] = f"Bearer {token}"
    
    response_sync = requests.post(url_sync, headers=headers_sync)
    
    if response_sync.status_code == 200:
        interlude_user = response_sync.json().get('interludeUser', {})
        balance_diamonds = interlude_user.get('balanceDiamonds', 0)
        print_info(f"Your Balance: {balance_diamonds}")
        return balance_diamonds
    else:
        print_error(f"Failed to update balance. Status Code: {response_sync.status_code}")
        return None

def fetch_upgrades(token, headers):
    url = "https://api.hamsterkombatgame.io/interlude/upgrades-for-buy"
    headers_request = headers['buyUpgradeRequest']
    headers_request['authorization'] = f"Bearer {token}"

    response = requests.post(url, headers=headers_request)

    if response.status_code == 200:
        upgrades = response.json().get('upgradesForBuy', [])
        print_success("Successfully fetched available upgrades.")
        
        # Save the response to an external file
        with open('upgrades_response.json', 'w') as file:
            json.dump(response.json(), file)

        # Extract upgrades and sort them based on profitPerHourDelta from highest to lowest
        sorted_upgrades = sorted(
            upgrades, 
            key=lambda x: x.get('profitPerHourDelta', 0), 
            reverse=True
        )

        # Extract only the IDs for each upgrade and sort them
        upgrade_ids = [upgrade['id'] for upgrade in sorted_upgrades]

        # Save the IDs to upgrade_ids.txt
        with open('upgrade_ids.txt', 'w') as file:
            for upgrade_id in upgrade_ids:
                file.write(f"{upgrade_id}\n")

        print("Saved upgrade IDs from highest to lowest in upgrade_ids.txt.")
        return sorted_upgrades  # Return the sorted upgrades

    else:
        print_error(f"Failed to fetch upgrades. Status Code: {response.status_code}")
        return None

def handle_account(init_data_raw, headers, extra_param=None):
    url = 'https://api.hamsterkombat.io/auth/auth-by-telegram-webapp'
    data = json.dumps({"initDataRaw": init_data_raw})

    response = requests.post(url, headers=headers['authRequest'], data=data)

    if response.status_code == 200:
        token = response.json().get('authToken')
        if token:
            url2 = "https://api.hamsterkombatgame.io/auth/account-info"
            headers2 = headers['accountInfoRequest']
            headers2['authorization'] = f"Bearer {token}"

            response2 = requests.post(url2, headers=headers2)

            if response2.status_code == 200:
                account_info = response2.json().get('accountInfo', {})
                name = account_info.get('name', 'User')
                print_success(f"Welcome, {name}!")
                
                balance_diamonds = update_balance(token, headers)  # Update balance once at the start of the process
                if balance_diamonds is not None:
                    print_account_info(name, balance_diamonds, "N/A")

                    # Fetch upgrades
                    upgrades = fetch_upgrades(token, headers)
                    if upgrades:
                        print_upgrade_status_with_number(upgrades)  # Use the new function with numbering
                        for upgrade in upgrades:
                            upgrade_id = upgrade['id']
                            # Prepare the request to buy the upgrade
                            url4 = "https://api.hamsterkombatgame.io/interlude/buy-upgrade"
                            payload = json.dumps({
                                "upgradeId": upgrade_id,
                                "timestamp": int(time.time() * 1000)
                            })
                            headers4 = headers['buyUpgradeRequest']
                            headers4['authorization'] = f"Bearer {token}"

                            response4 = requests.post(url4, headers=headers4, data=payload)

                            if response4.status_code == 200:
                                print_success(f"Successfully purchased upgrade {upgrade_id}.")
                            else:
                                error_response = response4.json()
                                if error_response.get('error_code') == 'INSUFFICIENT_FUNDS':
                                    if 'error_message' in error_response:
                                        error_message = error_response['error_message']
                                        required_match = re.search(r'required: ([\d.]+)', error_message)
                                        if required_match:
                                            required_funds = float(required_match.group(1))
                                            print_error(f"Insufficient balance to upgrade {upgrade_id}. Required: {required_funds}")
                                elif error_response.get('error_code') == 'UPGRADE_MAX_LEVEL':
                                    print_warning(f"Upgrade {upgrade_id} is at max level. Excluded.")
                                elif error_response.get('error_code') == 'UPGRADE_COOLDOWN':
                                    cooldown_seconds = error_response['cooldownSeconds']
                                    print_warning(f"Upgrade {upgrade_id} is in cooldown for {cooldown_seconds / 60:.2f} minutes.")
                                    
                            # Add delay after each purchase
                            print("Please wait 15 seconds...")
                            time.sleep(15)  # You can adjust the time as needed
                    else:
                        print("No upgrades found with profits.")
            else:
                print_error(f"Failed to get account info. Status Code: {response2.status_code}")
        else:
            print_error("Failed to get the token.")
    else:
        print_error(f"Failed to get the token. Status Code: {response.status_code}")

def get_token_for_account(init_data_raw, headers):
    return handle_account(init_data_raw, headers)  # Return the token only without executing upgrades
