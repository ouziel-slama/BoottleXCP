#! /usr/bin/env python3

import sys
import logging
import os
import decimal
import time
import json
import logging
import bottle
from bottle import route, run, template, Bottle, request, static_file, redirect, error, hook, response, abort, auth_basic

from counterpartyd.lib import (config, api, util, exceptions, bitcoin, blocks)
from counterpartyd.lib import (send, order, btcpay, issuance, broadcast, bet, dividend, burn, cancel, callback)

from helpers import set_options, init_logging, check_auth, D, S, DecimalEncoder, connect_to_db

from wsgiref import simple_server


set_options()
init_logging()
app = Bottle()
db = connect_to_db(10000)

@app.route('/<filename:path>')
@auth_basic(check_auth)
def send_static(filename):
    return static_file(filename, root=config.GUI_DIR)


@app.route('/')
@auth_basic(check_auth)
def index():
    return static_file("counterpartygui.html", root=config.GUI_DIR)


@app.route('/wallet')
@auth_basic(check_auth)
def wallet():
    wallet = {'addresses': {}}
    totals = {}
    for group in bitcoin.rpc('listaddressgroupings', []):
        for bunch in group:
            address, btc_balance = bunch[:2]
            get_address = util.get_address(db, address=address)
            balances = get_address['balances']
            assets =  {}
            empty = True
            if btc_balance:
                assets['BTC'] = btc_balance
                if 'BTC' in totals.keys(): totals['BTC'] += btc_balance
                else: totals['BTC'] = btc_balance
                empty = False
            for balance in balances:
                asset = balance['asset']
                balance = D(util.devise(db, balance['amount'], balance['asset'], 'output'))
                if balance:
                    if asset in totals.keys(): totals[asset] += balance
                    else: totals[asset] = balance
                    assets[asset] = balance
                    empty = False
            if not empty:
                wallet['addresses'][address] = assets

    wallet['totals'] = totals    
    response.content_type = 'application/json'
    return json.dumps(wallet, cls=DecimalEncoder)


@app.post('/action')
@auth_basic(check_auth)
def counterparty_action():

    unsigned = True if request.forms.get('unsigned')!=None and request.forms.get('unsigned')=="1" else False
    try:
        action = request.forms.get('action')

        if action=='send':
            source = request.forms.get('source')
            destination = request.forms.get('destination')
            asset = request.forms.get('asset')  
            quantity = util.devise(db, request.forms.get('quantity'), asset, 'input')      
            unsigned_tx_hex = send.create(db, source, destination, quantity, asset, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}       

        elif action=='order':
            source = request.forms.get('source')
            give_asset = request.forms.get('give_asset')
            get_asset = request.forms.get('get_asset')
            give_quantity = util.devise(db, request.forms.get('give_quantity'), give_asset, 'input')
            get_quantity = util.devise(db, request.forms.get('get_quantity'), get_asset, 'input')
            expiration = int(request.forms.get('expiration')) 
            fee_required = 0
            fee_provided = config.MIN_FEE
            if give_asset == 'BTC':
                fee_required = 0
                fee_provided = util.devise(db, request.forms.get('fee_provided'), 'BTC', 'input')
            elif get_asset == 'BTC':
                fee_required = util.devise(db, request.forms.get('fee_required'), 'BTC', 'input')
                fee_provided = config.MIN_FEE
         
            unsigned_tx_hex = order.create(db, source, give_asset,
                                           give_quantity, get_asset,
                                           get_quantity, expiration,
                                           fee_required, fee_provided,
                                           unsigned=unsigned)

            result = {'success':True, 'message':str(unsigned_tx_hex)}       

        elif action=='btcpay':
            order_match_id = request.forms.get('order_match_id')         
            unsigned_tx_hex = btcpay.create(db, order_match_id, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}          

        elif action=='cancel':
            offer_hash = request.forms.get('offer_hash')           
            unsigned_tx_hex = cancel.create(db, offer_hash, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='issuance':
            source = request.forms.get('source')
            destination = request.forms.get('destination')
            asset_name = request.forms.get('asset_name')
            divisible = True if request.forms.get('divisible')=="1" else False
            quantity = util.devise(db, request.forms.get('quantity'), None, 'input', divisible=divisible)

            callable_ = True if request.forms.get('callable')=="1" else False
            call_date = request.forms.get('call_date')
            call_price = request.forms.get('call_price')
            description = request.forms.get('description')
        
            if callable_:
                call_date = round(datetime.timestamp(dateutil.parser.parse(call_date)))
                call_price = float(call_price)
            else:
                call_date, call_price = 0, 0

            issuance.create(db, source, destination, asset_name, quantity, divisible, 
                            callable_, call_date, call_price, description, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}
        
        elif action=='dividend':
            source = request.forms.get('source')
            asset = request.forms.get('asset') 
            quantity_per_share = util.devise(db, request.forms.get('quantity_per_share'), 'XCP', 'input')
            unsigned_tx_hex = dividend.create(db, source, quantity_per_share, asset, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='callback':
            source = request.forms.get('source')
            asset = request.forms.get('asset')
            fraction_per_share = float(request.forms.get('fraction_per_share'))
            unsigned_tx_hex = callback.create(db, source, fraction_per_share, asset, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='broadcast':
            source = request.forms.get('source')
            text = request.forms.get('text')
            value = util.devise(db, request.forms.get('value'), 'value', 'input')
            fee_multiplier = request.forms.get('fee_multiplier')
            unsigned_tx_hex = broadcast.create(db, source, int(time.time()), value, fee_multiplier, text, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='bet':
            source = request.forms.get('source')
            feed_address = request.forms.get('feed_address')
            bet_type = int(request.forms.get('bet_type'))
            deadline = calendar.timegm(dateutil.parser.parse(request.forms.get('deadline')).utctimetuple())
            wager = util.devise(db, request.forms.get('wager'), 'XCP', 'input')
            counterwager = util.devise(db, request.forms.get('counterwager'), 'XCP', 'input')
            target_value = util.devise(db, request.forms.get('target_value'), 'value', 'input')
            leverage = util.devise(db, request.forms.get('leverage'), 'leverage', 'input')

            expiration = request.forms.get('expiration')
            unsigned_tx_hex = bet.create(db, source, feed_address, bet_type, deadline,
                                        wager, counterwager, target_value,
                                        leverage, expiration, unsigned=unsigned)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        else:
            result = {'success':False, 'message':'Unknown action.'} 

        if result['success']==True and unsigned==False:
            tx_hash = bitcoin.transmit(unsigned_tx_hex, ask=False);
            result['message'] = "Transaction transmited: "+tx_hash

    except Exception as e:
        result = {'success':False, 'message':str(e)} 

    response.content_type = 'application/json'
    return json.dumps(result, cls=DecimalEncoder)


def run_server():
    app.run(port=config.GUI_PORT, host=config.GUI_HOST, reloader=False)


if __name__ == '__main__':
    print("run server")
    run_server()




