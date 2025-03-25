<<<<<<< HEAD
import requests
import json
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Загрузка переменных окружения
load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.ataix.com"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Минимальный объём сделки (примерное значение, уточните на бирже)
MIN_ORDER_AMOUNT = 0.01

def get_balance(currency="USDT"):
    url = f"{BASE_URL}/api/user/balances/{currency}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            if data["error"] == "Permission denied":
                logging.error("Ошибка API: Permission denied. Проверьте доступ к DATA в настройках API-ключа.")
            else:
                logging.error(f"Ошибка API: {data['error']}")
            return 0
        return float(data.get("available", 0))
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении баланса: {e}")
        return 0

def get_trading_pair():
    url = f"{BASE_URL}/api/symbols"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        pairs = [pair for pair in data if pair.get("quoteCurrency") == "USDT" and float(pair.get("minPrice", float('inf'))) <= 0.6]
        return pairs[0]["symbol"] if pairs else None
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении торговых пар: {e}")
        return None

def get_max_bid_price(symbol):
    url = f"{BASE_URL}/api/book/{symbol}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        bids = data.get("bids", [])
        return max((float(order["price"]) for order in bids), default=0)
    except requests.RequestException as e:
        logging.error(f"Ошибка при получении стакана ордеров: {e}")
        return 0

def place_order(symbol, price, amount):
    url = f"{BASE_URL}/api/orders"
    order_data = {"symbol": symbol, "price": price, "quantity": amount, "side": "BUY"}
    try:
        response = requests.post(url, headers=HEADERS, data=json.dumps(order_data))
        response.raise_for_status()
        data = response.json()
        return {"id": data.get("id"), "status": "NEW"}
    except requests.RequestException as e:
        logging.error(f"Ошибка при размещении ордера: {e}")
        return {"id": None, "status": "FAILED"}

def main():
    balance = get_balance()
    logging.info(f"Доступный баланс: {balance:.2f} USDT")
    
    if balance == 0:
        logging.error("Баланс USDT равен нулю. Завершение работы.")
        return
    
    symbol = get_trading_pair()
    if not symbol:
        logging.error("Нет подходящей торговой пары.")
        return
    logging.info(f"Выбрана торговая пара: {symbol}")
    
    max_price = get_max_bid_price(symbol)
    if max_price == 0:
        logging.error("Не удалось определить максимальную цену покупки.")
        return
    logging.info(f"Максимальная цена покупки: {max_price:.6f} USDT")
    
    order_prices = [max_price * (1 - perc) for perc in [0.02, 0.05, 0.08]]
    orders = []

    for price in order_prices:
        amount = balance / 3 / price
        if amount < MIN_ORDER_AMOUNT:
            logging.warning(f"Пропускаем ордер: объём {amount:.6f} меньше минимального")
            continue
        order = place_order(symbol, price, amount)
        orders.append(order)
=======
import json
import requests
import re

# Укажите API-ключ здесь
API_KEY = "API ключ"  
BASE_URL = "https://api.ataix.kz"


def get_request(endpoint):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
    }
    print(f"📡 GET {url}")  # Лог запроса
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f"🔄 Response Code: {response.status_code}")
        print(f"📥 Response Body: {response.text[:500]}")  # Вывод первых 500 символов ответа
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return None


def post_request(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    print(f"📡 POST {url} с данными: {json.dumps(data, indent=2)}")  

    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        print(f"🔄 Response Code: {response.status_code}")
        print(f"📥 Response Body: {response.text[:500]}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return None


def get_balance(currency):
    data = get_request(f"/api/user/balances/{currency}")
    if not data:
        print("❌ Ошибка: баланс не получен")
        return 0
    
    print(f"✅ Баланс {currency}: {json.dumps(data, indent=2)}")
    
    match = re.search(r'"available"\s*:\s*"([\d.]+)"', json.dumps(data))
    return float(match.group(1)) if match else 0


def get_trading_pair():
    data = get_request("/api/symbols")
    
    if not data:
        print("❌ Ошибка: список торговых пар не получен")
        return None

    print(f"✅ Доступные пары: {json.dumps(data, indent=2)}")

    for pair in data:
        if isinstance(pair, dict) and pair.get("quote") == "USDT" and float(pair.get("minPrice", 1)) <= 0.6:
            print(f"🎯 Найдена подходящая пара: {pair.get('symbol')}")
            return pair.get("symbol")

    print("⚠️ Нет пары с ценой ≤ 0.6 USDT")
    return None


def get_highest_bid(symbol):
    data = get_request(f"/api/orderbook/{symbol}")
    if not data or "bids" not in data:
        print(f"❌ Ошибка: не удалось получить стакан для {symbol}")
        return 0

    print(f"✅ Стакан заявок: {json.dumps(data, indent=2)}")

    highest_bid = max(float(order["price"]) for order in data["bids"]) if data["bids"] else 0
    print(f"💰 Максимальная цена покупки: {highest_bid}")
    return highest_bid


def place_order(symbol, price, amount=10):
    order_data = {
        "symbol": symbol,
        "side": "buy",
        "type": "limit",
        "price": str(price),
        "quantity": str(amount)
    }
    response = post_request("/api/orders", order_data)

    if response:
        print(f"✅ Ордер размещён: {response}")
    else:
        print(f"❌ Ошибка размещения ордера {order_data}")

    return response


def main():
    print("🚀 Запуск скрипта...")

    usdt_balance = get_balance("USDT")
    print(f"🔹 Баланс USDT: {usdt_balance}")
    
    if usdt_balance <= 0:
        print("⚠️ Баланс USDT пустой или недоступен.")
        return
    
    pair = get_trading_pair()
    if not pair:
        print("⚠️ Нет подходящей торговой пары.")
        return
    
    highest_bid = get_highest_bid(pair)
    if highest_bid == 0:
        print("⚠️ Ошибка при получении максимальной цены ордера.")
        return
    
    order_prices = [
        round(highest_bid * 0.98, 6),
        round(highest_bid * 0.95, 6),
        round(highest_bid * 0.92, 6)
    ]
    
    orders = []
    for price in order_prices:
        order = place_order(pair, price)
        if order:
            orders.append({"order_id": order.get("id", "unknown"), "status": "NEW"})
>>>>>>> 1b1ab4c (Добавил основной код для работы с API Ataix)
    
    with open("orders.json", "w") as f:
        json.dump(orders, f, indent=4)
    
<<<<<<< HEAD
    logging.info("Ордера сохранены в orders.json")

if __name__ == "__main__":
    main()
=======
    print("✅ Ордеры успешно размещены и сохранены в orders.json")


if __name__ == "__main__":
    main()
>>>>>>> 1b1ab4c (Добавил основной код для работы с API Ataix)
