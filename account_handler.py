# account_handler.py
import json
import requests
import re
import time
from printer import print_error, print_success, print_info, print_warning

def print_account_info(name, balance_diamonds, upgrade_status):
    print(f"{'Account Name':<20}{'Diamonds Balance':<20}{'Upgrade Status':<20}")
    print(f"{'-'*60}")
    print(f"{name:<20}{balance_diamonds:<20}{upgrade_status:<20}")

def print_upgrade_status(upgrade_statuses):
    print(f"\n{'Upgrade ID':<25}{'Status':<25}{'Required Funds':<25}{'Cooldown (minutes)':<25}")
    print(f"{'-'*100}")
    for upgrade_id, status in upgrade_statuses.items():
        if status['reason'] == 'insufficient_funds':
            print(f"{upgrade_id:<25}{'Insufficient Funds':<25}{status['required_funds']:<25}{'N/A':<25}")
        elif status == "cooldown":
            print(f"{upgrade_id:<25}{'In Cooldown':<25}{'N/A':<25}{status['cooldown_seconds']/60:<25}")
        elif status == "max_level":
            print(f"{upgrade_id:<25}{'Max Level':<25}{'N/A':<25}{'N/A':<25}")
        else:
            print(f"{upgrade_id:<25}{'Upgraded':<25}{'N/A':<25}{'N/A':<25}")

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
        print_error(f"فشل في تحديث الرصيد. Status Code: {response_sync.status_code}")
        return None

def handle_account(init_data_raw, headers, upgrade_ids):
    url = 'https://api.hamsterkombat.io/auth/auth-by-telegram-webapp'
    data = json.dumps({"initDataRaw": init_data_raw})

    response = requests.post(url, headers=headers['authRequest'], data=data)

    if response.status_code == 200:
        token = response.json().get('authToken')
        if token:
            pending_upgrades = {}
            url2 = "https://api.hamsterkombatgame.io/auth/account-info"
            headers2 = headers['accountInfoRequest']
            headers2['authorization'] = f"Bearer {token}"

            response2 = requests.post(url2, headers=headers2)

            if response2.status_code == 200:
                account_info = response2.json().get('accountInfo', {})
                name = account_info.get('name', 'مستخدم')
                print_success(f"مرحبا بك، {name}!")
                
                balance_diamonds = update_balance(token, headers)  # تحديث الرصيد مرة واحدة فقط عند بدء العملية
                if balance_diamonds is not None:
                    print_account_info(name, balance_diamonds, "N/A")

                    # معالجة الترقيات
                    for upgrade_id in upgrade_ids:
                        # إعداد طلب شراء الترقية
                        url4 = "https://api.hamsterkombatgame.io/interlude/buy-upgrade"
                        payload = json.dumps({
                            "upgradeId": upgrade_id,
                            "timestamp": int(time.time() * 1000)
                        })
                        headers4 = headers['buyUpgradeRequest']
                        headers4['authorization'] = f"Bearer {token}"

                        response4 = requests.post(url4, headers=headers4, data=payload)

                        if response4.status_code == 200:
                            print_success(f"تم شراء الترقية {upgrade_id} بنجاح.")
                        else:
                            error_response = response4.json()
                            if error_response.get('error_code') == 'INSUFFICIENT_FUNDS':
                                if 'error_message' in error_response:
                                    error_message = error_response['error_message']
                                    required_match = re.search(r'required: ([\d.]+)', error_message)
                                    if required_match:
                                        required_funds = float(required_match.group(1))
                                        print_error(f"الرصيد غير كافي لترقية {upgrade_id}. المطلوب: {required_funds}")
                                        pending_upgrades[upgrade_id] = {
                                            "reason": "insufficient_funds",
                                            "required_funds": required_funds
                                        }
                            elif error_response.get('error_code') == 'UPGRADE_MAX_LEVEL':
                                print_warning(f"ترقية {upgrade_id} في أقصى مستوى. تم استبعادها.")
                                pending_upgrades[upgrade_id] = {"reason": "max_level"}
                            elif error_response.get('error_code') == 'UPGRADE_COOLDOWN':
                                cooldown_seconds = error_response['cooldownSeconds']
                                print_warning(f"ترقية {upgrade_id} في فترة الانتظار لمدة {cooldown_seconds / 60:.2f} دقيقة.")
                                pending_upgrades[upgrade_id] = {
                                    "reason": "cooldown",
                                    "cooldown_seconds": cooldown_seconds  # قم بتخزين الوقت المتبقي هنا
                                }

                    # طباعة حالة الترقيات
                    print_upgrade_status(pending_upgrades)

            else:
                print_error(f"فشل في الحصول على معلومات الحساب. Status Code: {response2.status_code}")
        else:
            print_error("فشل في الحصول على التوكن.")
    else:
        print_error(f"فشل في الحصول على التوكن. Status Code: {response.status_code}")

def get_token_for_account(init_data_raw, headers):
    return handle_account(init_data_raw, headers, [])  # إرجاع التوكن فقط دون تنفيذ الترقيات