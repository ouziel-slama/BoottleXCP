#! /usr/bin/env python3

import sys
import traceback
import logging
import os
import decimal
import time
import json
import logging
import bottle
from bottle import route, run, template, Bottle, request, static_file, redirect, error, hook, response, abort, auth_basic

from counterpartyd.lib import (config, util, exceptions, bitcoin)
from counterpartyd.lib import (send, order, btcpay, issuance, broadcast, bet, dividend, burn, cancel, callback)

from helpers import set_options, init_logging, D, S, DecimalEncoder, connect_to_db, check_auth, wallet_unlock


app = Bottle()
set_options()
init_logging()
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

def getp(key, default=''):    
    value = request.forms.get(key)
    if value is None or value=='':
        return default
    return value

@app.post('/action')
@auth_basic(check_auth)
def counterparty_action():

    unsigned = True if getp('unsigned')!=None and getp('unsigned')=="1" else False
    try:             
        passphrase = getp('passphrase', None)      
        unlock = wallet_unlock(passphrase)
        if unlock['success']==False:
            raise Exception(unlock['message'])

        action = getp('action') 

        if action=='send':
            source = getp('source')
            destination = getp('destination')
            asset = getp('asset')  
            quantity = util.devise(db, getp('quantity'), asset, 'input')
            tx_info = send.compose(db, source, destination, asset, quantity)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}       

        elif action=='order':
            source = getp('source')
            give_asset = getp('give_asset')
            get_asset = getp('get_asset')
            fee_fraction_required  = getp('fee_fraction_required', '0')
            fee_fraction_provided = getp('fee_fraction_provided', '0')
            give_quantity = getp('give_quantity', '0')
            get_quantity = getp('get_quantity', '0')
            try:
                expiration = int(getp('expiration')) 
            except:
                raise Exception('Invalid expiration')

            # Fee argument is either fee_required or fee_provided, as necessary.
            if give_asset == 'BTC':
                fee_required = 0
                fee_fraction_provided = util.devise(db, fee_fraction_provided, 'fraction', 'input')
                fee_provided = round(D(fee_fraction_provided) * D(give_quantity) * D(config.UNIT))
                if fee_provided < config.MIN_FEE:
                    raise Exception('Fee provided less than minimum necessary for acceptance in a block.')
            elif get_asset == 'BTC':
                fee_provided = config.MIN_FEE
                fee_fraction_required = util.devise(db, fee_fraction_required, 'fraction', 'input')
                fee_required = round(D(fee_fraction_required) * D(get_quantity) * D(config.UNIT))
            else:
                fee_required = 0
                fee_provided = config.MIN_FEE

            give_quantity = util.devise(db, D(give_quantity), give_asset, 'input')
            get_quantity = util.devise(db, D(get_quantity), get_asset, 'input') 
            tx_info = order.compose(db, source, give_asset,
                                    give_quantity, get_asset,
                                    get_quantity, expiration,
                                    fee_required, fee_provided)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)

            result = {'success':True, 'message':str(unsigned_tx_hex)} 

        elif action=='btcpay':
            order_match_id = getp('order_match_id')
            tx_info = btcpay.compose(db, order_match_id)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}          

        elif action=='cancel':
            offer_hash = getp('offer_hash')                     
            tx_info = cancel.compose(db, offer_hash)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='issuance':
            source = getp('source')
            transfer_destination = getp('transfer_destination')
            asset_name = getp('asset_name')
            divisible = True if getp('divisible')=="1" else False
            quantity = util.devise(db, getp('quantity'), None, 'input', divisible=divisible)

            callable_ = True if getp('callable')=="1" else False
            call_date = getp('call_date')
            call_price = getp('call_price')
            description = getp('description')

            if callable_:
                if call_date=='':
                    raise Exception('must specify call date of callable asset')
                if call_price=='':
                    raise Exception('must specify call price of callable asset')
                call_date = calendar.timegm(dateutil.parser.parse(args.call_date).utctimetuple())
                call_price = float(args.call_price)
            else:
                call_date, call_price = 0, 0

            try:
                quantity = int(quantity)
            except ValueError:
                raise Exception("Invalid quantity")
            tx_info = issuance.compose(db, source, transfer_destination,
                                       asset_name, quantity, divisible, callable_,
                                       call_date, call_price, description)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}
        
        elif action=='dividend':
            source = getp('source')
            asset = getp('asset') 
            quantity_per_share = util.devise(db, getp('quantity_per_share'), 'XCP', 'input')
            tx_info = dividend.compose(db, source, quantity_per_unit, asset)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='callback':
            source = getp('source')
            asset = getp('asset')
            fraction_per_share = util.devise(db, getp('fraction_per_share'), 'fraction', 'input')
            tx_info = callback.compose(db, source, fraction_per_share, asset)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='broadcast':
            source = getp('source')
            text = getp('text')
            value = util.devise(db, getp('value'), 'value', 'input')
            fee_fraction = util.devise(db, getp('fee_fraction'), 'fraction', 'input')
            tx_info = broadcast.compose(db, source, int(time.time()), value, fee_fraction, text)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        elif action=='bet':
            source = getp('source')
            feed_address = getp('feed_address')
            bet_type = int(getp('bet_type'))
            deadline = calendar.timegm(dateutil.parser.parse(getp('deadline')).utctimetuple())
            wager = util.devise(db, getp('wager'), 'XCP', 'input')
            counterwager = util.devise(db, getp('counterwager'), 'XCP', 'input')
            target_value = util.devise(db, getp('target_value'), 'value', 'input')
            leverage = util.devise(db, getp('leverage'), 'leverage', 'input')
            expiration = getp('expiration')
            tx_info = bet.compose(db, source, feed_address,
                                  bet_type, deadline, wager,
                                  counterwager, target_value,
                                  leverage, expiration)
            unsigned_tx_hex = bitcoin.transaction(tx_info, config.MULTISIG)
            result = {'success':True, 'message':str(unsigned_tx_hex)}

        else:
            result = {'success':False, 'message':'Unknown action.'} 

        if result['success']==True and unsigned==False:
            tx_hash = bitcoin.transmit(unsigned_tx_hex);
            result['message'] = "Transaction transmited: "+tx_hash

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_tb(exc_traceback, limit=5)
        message = str(e)
        print(message)
        result = {'success':False, 'message':message} 

    response.content_type = 'application/json'
    return json.dumps(result, cls=DecimalEncoder)


def run_server():
    app.run(port=config.GUI_PORT, host=config.GUI_HOST)


if __name__ == '__main__':
    run_server()




