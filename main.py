# main.py
import json
import time
import threading
from account_handler import handle_account, update_balance, get_token_for_account
from printer import print_info

# قراءة الرؤوس من ملف JSON
with open('headers.json', 'r') as headers_file:
    headers = json.load(headers_file)

# قراءة قائمة الترقيات من ملف نصي
with open('upgrade_ids.txt', 'r') as file:
    upgrade_ids = [line.strip() for line in file.readlines() if line.strip()]

# التشغيل التلقائي لكل حساب
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

        # تحديث الرصيد كل 5 دقائق خلال فترة الانتظار
        for i in range(1):
            #print_info(f"انتظار تحديث الرصيد بعد 5 دقائق ({i+1}/12)")
            time.sleep(3)

            # تمرير كل من token و headers إلى update_balance
            for init_data_raw in init_data_list:
                init_data_raw = init_data_raw.strip()
                if init_data_raw:
                    # استخدام نفس الـ token الذي تم الحصول عليه لكل حساب
                    token = get_token_for_account(init_data_raw, headers)
                    if token:
                        thread = threading.Thread(target=update_balance, args=(token, headers))
                        thread.start()

        print_info("Please wait 1 hour ")
        time.sleep(3600)