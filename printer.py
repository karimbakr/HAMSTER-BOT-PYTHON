# printer.py
from colorama import Fore, init

# تهيئة Colorama
init(autoreset=True)

def print_error(message):
    print(f"{Fore.RED}{message}")

def print_success(message):
    print(f"{Fore.GREEN}{message}")

def print_info(message):
    print(f"{Fore.YELLOW}{message}")

def print_warning(message):
    print(f"{Fore.MAGENTA}{message}")