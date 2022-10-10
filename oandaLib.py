#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# system imports

import sys
import os
import math
import datetime
import time

# OANDA library functions

import oandapyV20
import oandapyV20.endpoints
import oandapyV20.contrib
import oandapyV20.endpoints.accounts as v20Accounts
import oandapyV20.endpoints.instruments as v20Instruments
import oandapyV20.endpoints.pricing as v20Pricing
import oandapyV20.endpoints.orders as v20Orders
import oandapyV20.endpoints.positions as v20Positions
import oandapyV20.endpoints.trades as v20Trades
import oandapyV20.contrib.requests as v20Requests

# The Oanda class is actually a self emcompassing object that wraps all
# of OANDA's functionality into a neat little package.

class oanda:
    # Define the special variables for this object. ALL variable WITHIN
    # the class must have the prefix of self. self defines the internal
    # mechanics that help isolate variables.

    # Initialize the object and automatically get everything set up
    def __init__(self,fname=None):
        self.Credentials=self.GetCredentials(fname)
        self.Broker=self.Login()
        self.Markets=self.GetMarkets()

    # Load credentials from file

    def GetCredentials(self,fname):
        Credentials={}
        if os.path.exists(fname):
            try:
                FileHandle=open(fname,'r')
                Credentials['AccountID']=FileHandle.readline().strip()
                Credentials['BearerToken']=FileHandle.readline().strip()
                FileHandle.close()
            except:
                print("Please check your credentials.txt file, missing or malformed data.")
                sys.exit(1)
        else:
            print("You must save your OANDA account crdentials to: credentials.txt")
            sys.exit(1)

        return Credentials

    # Login to the exchange

    def Login(self):
        try:
            oanda=oandapyV20.API(access_token=self.Credentials['BearerToken'])
        except Exception as err:
            print("Error: ",str(err))
            sys.exit(1)

        return oanda

    # Handle all OANDA requests with a retry loop

    def API(self,function,req):
        retry=0
        RetryLimit=3

        done=False
        while not done:
            try:
                result=self.Broker.request(req)
            except Exception as err:
                if retry>RetryLimit:
                    print(str(err))
                    sys.exit(1)
                else:
                    em=str(err)
                    print(f"{function}: Retrying ({retry+1}), {em}")
            else:
                done=True
            retry+=1

        return result

    def GetMarkets(self):
        req=v20Accounts.AccountInstruments(accountID=self.Credentials['AccountID'])
        results=self.API("GetMarket",req)

        return results

    # OANDA request to pull ticker data

    def GetTicker(self,symbol):
        params={ "instruments":symbol }
        req=v20Pricing.PricingInfo(accountID=self.Credentials['AccountID'],params=params)
        ticker=self.API("GetTicker",req)

        # Build the forex pair dictionary

        ForexPair={}
        ForexPair['Ask']=round(float(ticker['prices'][0]['asks'][0]['price']),5)
        ForexPair['Bid']=round(float(ticker['prices'][0]['bids'][0]['price']),5)
        ForexPair['Spread']=round(ForexPair['Ask']-ForexPair['Bid'],5)

        return ForexPair

    # Read the order book

    def GetOrderBook(self,symbol):
        req=v20Instruments.InstrumentsOrderBook(instrument=symbol,params={})
        results=self.API("GetOrderBook",req)
        return results['orderBook']['buckets']

    # Read the currnt open positions

    def GetPositionsUnits(self,symbol):
        symbol=symbol.replace('/','_').upper()

        req=v20Positions.OpenPositions(self.Credentials['AccountID'])
        results=self.API("GetPosiions",req)
        if results!=None:
            for pos in results['positions']:
                asset=pos['instrument']
                if symbol==asset:
                    if 'averagePrice' in pos['long']:
                        units=float(pos['long']['units'])
                    else:
                        units=-(float(pos['short']['units']))
                    return units
        return 0

    def GetBalance(self):
        req=v20Accounts.AccountSummary(accountID=self.Credentials['AccountID'])
        results=self.API("GetBalance",req)
        return float(results['account']['balance'])

    # Place order. Return order ID and DON'T wait on limit orders. That needs
    # to be a separate functionality.
    #
    # Arg sequence:
    #   symbol, type, side (action), amount, price
    #
    # PlaceOrder(exchange, Active, pair=pair, orderType=orderType, action=action, amount=amount, 
    #   close=close, ReduceOnly=ReduceOnly, LedgerNote=ledgerNote)
    #
    # IMPORTANT: buy and sell are TWO DIFFERENT END POINTS
    #
    # Market orders are fill or kill (FOK) for timeInForce by default. GTC will NOT work.

    def PlaceOrder(self,pair,orderType,action,amount,price):
        pair=pair.replace('/','_')
        orderType=orderType.upper()
        action=action.lower()

        if(action=='buy'):
            order={}
            if orderType=='LIMIT':
                order['price']=str(price)
                order['timeInForce']='GTC'
            order['units']=str(amount)
            order['instrument']=pair
            order['type']=orderType
            order['positionFill']='DEFAULT'
            params={}
            params['order']=order

            res=v20Orders.OrderCreate(self.Credentials['AccountID'],data=params)
            results=self.API("OrderCreate",res)
        elif (action=='sell'):
            params={}
            if str(amount).upper()!='ALL':
                # amount is STR, need float for abs()
                amount=float(amount)
                if float(amount)>=0:
                    params['longUnits']=str(math.floor(abs(amount)))
                else:
                    params['shortUnits']=str(math.floor(abs(amount)))
            else:
                params['longUnits']="ALL"
            res=v20Positions.PositionClose(self.Credentials['AccountID'],instrument=pair,data=params)
            results=self.API("PositionClose",res)
        else:
            print("PlaceOrder","Action is neither BUY nor SELL")
            sys.exit(1)
        return results

