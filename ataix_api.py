import json, re, requests, sys, os 

API_KEY = "api_key"

def get_request(endpoint):
    url = f"https://api.ataix.kz{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
    }
    response = requests.get(url, headers=headers, timeout=20)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def find_name_currencies(text, word):
    words = re.findall(r'\b\w+\b', text)
    unique_currencies = set()
    for i in range(len(words) - 1):
        if words[i] == word:
            next_word = re.sub(r'[^a-zA-Zа-яА-Я]', '', words[i + 1])
            unique_currencies.add(next_word)
    return unique_currencies

name_currencies = find_name_currencies(json.dumps(get_request("/api/symbols")), "base")
if name_currencies:
    print("Доступный баланс на бирже в токенах USDT")
    for currency in name_currencies:
        balance_info = get_request(f"/api/user/balances/{currency}")
        if balance_info:
            balance = re.search(r"'available':\s*'([\d.]+)'", str(balance_info))
            if balance:
                print(currency, "\t\t", balance.group(1))

def find_symbols(text, word):
    words = re.findall(r'\b\w+(?:/\w+)?\b', text)
    pair_sym = []
    for i in range(len(words) - 1):
        if words[i] == word:
            next_word = words[i + 1]
            pair_sym.append(next_word)
    return pair_sym

def find_prices(text, word):
    pattern = rf'{word}[\s\W]*([-+]?\d*\.\d+|\d+)'
    matches = re.findall(pattern, text)
    return matches

currencies_less_0_6 = []
price_less_0_6_list = {}
symbols = find_symbols(json.dumps(get_request("/api/symbols")), "symbol")
price = find_prices(json.dumps(get_request("/api/prices")), "lastTrade")
if symbols and price:
    for i in range(len(symbols)):
        if "USDT" in symbols[i] and float(price[i]) <= 0.6:
            currencies_less_0_6.append(symbols[i])
            price_less_0_6_list[symbols[i]] = price[i]

if currencies_less_0_6:
    while True:
        current_cur = input("Выберите торговую пару (TRX, IMX, 1INCH) --> ").upper()
        if current_cur + "/USDT" in currencies_less_0_6:
            price_less_0_6 = price_less_0_6_list[current_cur + "/USDT"]
            break
        elif current_cur == "EXIT":
            sys.exit()
        else:
            print("Такой торговой пары нет в списке")

    print(current_cur, "\t\t", price_less_0_6)
    price_2pc = round(float(price_less_0_6) * 0.98, 4)
    price_5pc = round(float(price_less_0_6) * 0.95, 4)
    price_8pc = round(float(price_less_0_6) * 0.92, 4)
    print(f"Следующим шагом будет создано три ордера на покупку токена {current_cur},\nбудет куплено по одному токену с уменьшением цены на\n2%({price_2pc}$), 5%,({price_5pc}$) 8%({price_8pc}$)\nЕсли Вы согласны напишите \"y\"")

    while True:
        x = input("--> ")
        if x == "y":
            break
        elif x == "exit":
            sys.exit()

    def post_orders(symbol, price):
        url = "https://api.ataix.kz/api/orders"
        headers = {
            "accept": "application/json",
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "symbol": symbol,
            "side": "buy",
            "type": "limit",
            "quantity": 1,
            "price": price
        }
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    order_2pc = post_orders(current_cur + "/USDT", price_2pc)
    order_5pc = post_orders(current_cur + "/USDT", price_5pc)
    order_8pc = post_orders(current_cur + "/USDT", price_8pc)

    orders_list = [order_2pc, order_5pc, order_8pc]

    filename = "orders_data.json"

    if os.path.exists(filename):
        with open(filename, "r") as file:
            try:
                orders = json.load(file)
            except json.JSONDecodeError:
                orders = []
    else:
        orders = []

    for order in orders_list:
        if order:
            order_data = {
                "orderID": order["result"]["orderID"],
                "price": order["result"]["price"],
                "quantity": order["result"]["quantity"],
                "symbol": order["result"]["symbol"],
                "created": order["result"]["created"],
                "status": order["result"].get("status", "NEW")
            }
            orders.append(order_data)

    with open(filename, "w") as file:
        json.dump(orders, file, indent=4)

    print("[+]Ордера успешно созданы. Для проверки результата посетите сайт ATAIX, вкладка \"Мои ордера\". Данные успешно сохранены в", filename)
