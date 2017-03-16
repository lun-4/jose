#!/usr/bin/env python3

import sys
sys.path.append("..")
import josecommon as jcommon
import jauxiliar as jaux
import joseconfig as jconfig

from random import SystemRandom
random = SystemRandom()

import time
import decimal
import asyncio
import wolframalpha
import pyowm
import traceback

COINDESK_API = 'https://api.coindesk.com/v1/bpi'
COINDESK_CURRENT_URL = '{}/currentprice.json'.format(COINDESK_API)
COINDESK_CURRENCYLIST_URL = '{}/supported-currencies.json'.format(COINDESK_API)
COINDESK_CURRENCY_URL = '{}/currentprice/%s.json'.format(COINDESK_API)

COMMONCRYPTO = ['BTC', 'ETH', 'DASH', 'LTC', 'XMR', 'XRP', 'DOGE', 'REP', 'LSK']
COMMON_WORLD = ['USD', 'GBP', 'EUR', 'JPY', 'CAD']
COMMON_CURRENCIES = COMMONCRYPTO + COMMON_WORLD

CRYPTOAPI_HELPURL = 'https://www.cryptocompare.com/api'
CRYPTOAPI_MULTIPRICE = 'https://min-api.cryptocompare.com/data/pricemulti?fsyms=%s&tsyms=%s'
CRYPTOAPI_ONEPRICE = 'https://min-api.cryptocompare.com/data/price?fsym=%s&tsyms=%s'

class JoseMath(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)
        self.wac = wolframalpha.Client(jconfig.WOLFRAMALPHA_APP_ID)
        self.owm = pyowm.OWM(jconfig.OWM_APIKEY)
        self.btc_supported = []
        self.btc_cache = None

        # 30 minutes
        self.cbk_new('jmath.cryptocache', self.crypto_cache, 1800)

    async def crypto_cache(self):
        cryptostr = ','.join(COMMONCRYPTO)
        currencystr = ','.join(COMMON_WORLD)
        url = CRYPTOAPI_MULTIPRICE % (cryptostr, currencystr)

        try:
            priceinfo = await self.json_from_url(url)
            self.btc_cache = priceinfo
        except asyncio.TimeoutError as err:
            self.logger.warning("[crypto_cache]: TimeoutError: %r", err)
        except Exception as err:
            self.logger.error("[crypto_cache]: %r", err)

    async def ext_load(self):
        # try to get from coindesk supported currencies
        try:
            try:
                currency_data = await self.json_from_url(COINDESK_CURRENCYLIST_URL)
            except Exception as err:
                self.logger.warning("[jmath:currency_list] err, going fallback", exc_info=True)
                currency_data = [{'currency': 'USD'}, {'currency': 'GBP'}, {'currency': 'EUR'}]

            for currency in currency_data:
                currency_symbol = currency['currency']
                self.btc_supported.append(currency_symbol)

            return True, ''
        except Exception as err:
            return False, repr(err)

    async def ext_unload(self):
        self.cbk_remove('jmath.cryptocache')
        del self.wac, self.owm, self.btc_supported
        return True, ''

    async def c_wolframalpha(self, message, args, cxt):
        '''`j!wolframalpha terms` - make a request to Wolfram|Alpha'''
        if len(args) < 2:
            await cxt.say(self.c_wolframalpha.__doc__)
            return

        term_to_wolfram = ' '.join(args[1:])
        if len(term_to_wolfram.strip()) < 1:
            await cxt.say("haha no")
            return

        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

        self.logger.info("Wolfram|Alpha: %s", term_to_wolfram)

        await cxt.send_typing()

        future = self.loop.run_in_executor(None, \
            self.wac.query, term_to_wolfram)
        try:
            res = await asyncio.wait_for(future, 13)
        except asyncio.TimeoutError:
            await cxt.say("`[wolframalpha] Timeout reached`")

        if getattr(res, 'results', False):
            try:
                pods = (pod for pod in res.pods)
                pod = next(pods)
                while pod.title == 'Input interpretation':
                    pod = next(pods)
                text = None

                if getattr(pod, 'text', False):
                    text = pod.text
                elif pod.get('subpod', False):
                    subpod = pod['subpod']
                    text = subpod['img']['@src']
                else:
                    text = None
                    pass

                if text is not None:
                    await cxt.say("%s:\n%s", (term_to_wolfram, text))
                else:
                    await cxt.say(":poop: `%r`", (pod,))
                return
            except Exception as e:
                await cxt.say(self.codeblock("", traceback.format_exc()))
        else:
            await cxt.say(":cyclone: Sem resposta :cyclone:")
            return

    async def c_wa(self, message, args, cxt):
        '''`j!wa terms` - alias para `!wolframalpha`'''
        await self.c_wolframalpha(message, args, cxt)

    async def c_temperature(self, message, args, cxt):
        '''`j!temperature location` - temperature data from OpenWeatherMap'''
        # ratelimit 60/minute
        if len(args) < 2:
            await cxt.say(self.c_temperature.__doc__)
            return

        location = ' '.join(args[1:])

        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

        try:
            future = self.loop.run_in_executor(None, \
                self.owm.weather_at_place, location)
            observation = await future
        except:
            await cxt.say("Erro tentando conseguir a temperatura para esse local")
            return
        w = observation.get_weather()

        tempkelvin = w.get_temperature()
        tempcelsius = w.get_temperature("celsius")
        tempfahren = w.get_temperature("fahrenheit")

        celsiusnow = tempcelsius['temp']
        fahnow = tempfahren['temp']
        kelnow = tempkelvin['temp']

        await cxt.say("`%s` is at `%s °C, %s °F, %s °K`", \
            (location, celsiusnow, fahnow, kelnow))

    async def c_temp(self, message, args, cxt):
        '''`j!temp location` - alias para `!temperature`'''
        await self.c_temperature(message, args, cxt)

    async def c_therm(self, message, args, cxt):
        '''`j!therm location` - alias para `!temperature`'''
        await self.c_temperature(message, args, cxt)

    def lewd(self, n):
        num = 3
        t = 0
        while t != n:
            lewd = num ** 2 - 2
            for a in range(2, lewd):
                if lewd % a == 0:
                    break
            else:
                yield num
                t += 1
            num += 6

    async def c_lewd(self, message, args, cxt):
        '''`j!lewd n` - shows the `n` lewd numbers'''
        if len(args) < 2:
            await cxt.say(self.c_lewd.__doc__)

        try:
            n = int(args[1])
        except Exception as e:
            await cxt.say("Error parsing arguments: %r", (e,))
            return

        if n > 30:
            await cxt.say("nope")
            return

        await cxt.say(self.codeblock("", list(self.lewd(n))))

    async def c_money(self, message, args, cxt):
        '''`j!money amount base to` - Converts money, with `base` and `to` being currencies.
`!money list` - list all available currencies'''

        if len(args) > 1:
            if args[1] == 'list':
                data = await self.json_from_url("http://api.fixer.io/latest")
                await cxt.say(self.codeblock("", " ".join(data["rates"])))
                return

        if len(args) < 3:
            await cxt.say(self.c_money.__doc__)
            return

        try:
            amount = float(args[1])
        except Exception as e:
            await cxt.say("Error parsing `amount`")
            return

        try:
            currency_from = args[2].upper()
            currency_to = args[3].upper()
        except:
            await cxt.say(self.c_money.__doc__)
            return

        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

        url = "http://api.fixer.io/latest?base={}".format(currency_from.upper())
        data = await self.json_from_url(url)

        if 'error' in data:
            await cxt.say("money API error: %s", (data['error'],))
            return

        if currency_to not in data['rates']:
            await cxt.say("Invalid currency to convert to: %s", (currency_to,))
            return

        rate = data['rates'][currency_to]
        res = amount * rate

        await cxt.say('{} {} = {} {}'.format(
            amount, currency_from, res, currency_to
        ))

    async def c_bitcoin(self, message, args, cxt):
        '''`j!bitcoin [amount=1] [currency=USD]` - Get XBP price info'''

        # parse args
        try:
            btc_amount = float(args[1])
        except:
            btc_amount = 1

        try:
            currency = args[2].upper()
        except:
            currency = 'USD'

        # get data from coindesk
        self.logger.info("[bitcoin] %d BTC to %s", btc_amount, currency)
        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)

        data = await self.json_from_url(COINDESK_CURRENT_URL)

        if currency not in ['USD', 'GBP', 'EUR']:
            if currency not in self.btc_supported:
                await cxt.say("%s: Currency not supported", (currency,))
                return

            data = await self.json_from_url(COINDESK_CURRENCY_URL % currency)

        rate = float(data['bpi'][currency]['rate_float'])
        desc = data['bpi'][currency]['description']
        amount = rate * btc_amount

        await cxt.say("{} BTC = {} {}(*{}*), Powered by https://coindesk.com/price" \
            .format(btc_amount, amount, currency, desc))

    async def c_btc(self, message, args, cxt):
        '''`j!btc` - alias for `j!bitcoin`'''
        await self.c_bitcoin(message, args, cxt)

    async def c_crypto(self, message, args, cxt):
        '''`j!crypto amount=1 from=BTC to=USD` - converts cryptocurrencies pricing'''

        if len(args) < 3:
            await cxt.say(self.c_crypto.__doc__)
            return

        try:
            amount = decimal.Decimal(args[1])
        except:
            amount = 1

        try:
            from_currency = args[2].upper()
        except:
            from_currency = 'BTC'

        try:
            to_currency = args[3].upper()
        except:
            to_currency = 'USD'

        self.logger.info("[crypto] %.2f %s to %s", amount, \
            from_currency, to_currency)

        await self.jcoin_pricing(cxt, jcommon.API_TAX_PRICE)
        try:
            data = dict(self.btc_cache)
        except TypeError as err:
            await cxt.say(":warning: Cache error, probably API having issues `%r`", err)
            return

        nocache = False
        rate = None

        # up do date data
        if (from_currency not in COMMON_CURRENCIES) or (to_currency not in COMMON_CURRENCIES):
            data = await self.json_from_url(CRYPTOAPI_ONEPRICE % (from_currency, to_currency))
            nocache = True

        try:
            if nocache:
                rate = decimal.Decimal(data[to_currency])
            else:
                rate = decimal.Decimal(data[from_currency][to_currency])
        except Exception as err:
            await cxt.say('`%r`', (err,))
            return

        result = decimal.Decimal(amount * rate)
        await cxt.say("{:.4g} {} = {:.4g} {}, Powered by: {}".format(amount, \
            from_currency, result, to_currency, CRYPTOAPI_HELPURL))

    async def c_roll(self, message, args, cxt):
        '''`j!roll <amount>d<sides>` - roll fucking dice'''
        if len(args) < 2:
            await cxt.say(self.c_roll.__doc__)
            return

        dicestr = args[1]
        dice = dicestr.split('d')
        dice_amount = 1
        dice_sides = 6

        try:
            if dice[0] != '':
                dice_amount = int(dice[0])
        except ValueError:
            await cxt.say("try to do your things better(dice_amount).")
            return

        try:
            dice_sides = int(dice[1])
        except ValueError:
            await cxt.say("try to do your things better(dice_sides).")
            return

        if dice_amount <= 0 or dice_sides <= 0:
            await cxt.say("nonono")
            return

        if dice_amount > 100:
            await cxt.say("100+ dice? nonono")
            return

        if dice_sides > 50:
            await cxt.say("50+ sides? nonono")
            return

        dices = []
        for i in range(dice_amount):
            dice_result = random.randint(1, dice_sides)
            dices.append(dice_result)

        await cxt.say("%s: `%s` => %d", (dicestr, \
            ', '.join(str(r) for r in dices), sum(dices)))

    async def c_percent(self, message, args, cxt):
        '''`j!percent percentage amount` - Calculate percentages out of stuff'''

        if len(args) < 3:
            await cxt.say(self.c_percent.__doc__)
            return

        try:
            percentage = decimal.Decimal(args[1])
        except:
            await cxt.say("Error parsing `percentage`")
            return

        try:
            amount = decimal.Decimal(args[2])
        except:
            await cxt.say("Error parsing `amount`")
            return

        res = (percentage * amount) / decimal.Decimal(100)
        await cxt.say("%.2f%% out of %.2f = **%.4f**", (percentage, amount, res))

    async def c_mkping(self, message, args, cxt):
        '''`j!mkping amount` - makes a better ping to discord'''
        await self.is_admin(message.author.id)

        try:
            amount = int(args[1])
        except:
            await cxt.say(self.c_mkping.__doc__)
            return

        if amount < 1 or amount > 40:
            await cxt.say("`amount` out of range `[1-40]`")
            return

        pings = []
        for i in range(amount):
            t_init = time.time()
            await cxt.send_typing()
            t_final = time.time()

            delta = (t_final - t_init) * 1000
            pings.append(delta)

            await asyncio.sleep(0.5)

        average_ms = (sum(pings) / len(pings))
        await cxt.say("Average over %d pings: %.2fms max/min: %.2fms/%.2fms", \
            (amount, average_ms, max(pings), min(pings)))
