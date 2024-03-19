from polosdk import RestClient

class Trader:
    def __init__(self, stable, coin, apikey, secret):
        self.stable = stable
        self.coin = coin
        self.stable_balance = 0
        self.coin_balance = 0
        self.apikey = apikey
        self.secret = secret
        self.client = RestClient(apikey, secret)
    
    def get_balances(self):
        balances = self.client.accounts().get_balances()[0]["balances"]
        
        for item in balances:
            if item["currency"] == self.stable:
                stable_balance = float(item["available"])
            elif item["currency"] == self.coin:
                coin_balance = float(item["available"])

        return stable_balance, coin_balance

    def create_order(self, amount, side, symbol):
        order_response = ""
        if side == "BUY":
            order_response = self.client.orders().create(side=side, amount=amount, symbol=symbol)
        elif side == "SELL":
            order_response = self.client.orders().create(side=side, quantity=amount, symbol=symbol)
        response = self.client.orders().get_by_id(order_id=order_response["id"])
        if response["state"] == "FILLED":
            return True
        else:
            return False

    def buy(self, amount):
        amount = str(amount)
        print(f"Buying {amount} {self.stable} of {self.coin}...")
        
        if self.create_order(str(round(float(amount), 2)), "BUY", f'{self.coin}_{self.stable}'):
            print("Bought!")
        else:
            print("Error while buying!")
            
        stable_balance, coin_balance = self.get_balances()
        print(f'Total balance of {self.stable}: {stable_balance} {self.stable}')
        print(f'Total balance of {self.coin}: {coin_balance} {self.coin}')

    def sell(self, amount):
        amount = str(amount)
        print(f"Selling {amount} {self.coin}...")

        if self.create_order(str(round(float(amount), 2)), "SELL", f'{self.coin}_{self.stable}'):
            print("Sold!")
        else:
            print("Error while buying!")
        
        stable_balance, coin_balance = self.get_balances()
        print(f'Total balance of {self.stable}: {stable_balance} {self.stable}')
        print(f'Total balance of {self.coin}: {coin_balance} {self.coin}')