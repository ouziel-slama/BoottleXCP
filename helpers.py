import os
import logging
import json
import configparser
import appdirs
import decimal
import apsw
from counterpartyd.lib import config, util, bitcoin

D = decimal.Decimal


def set_options (data_dir=None, bitcoind_rpc_connect=None, bitcoind_rpc_port=None,
                 bitcoind_rpc_user=None, bitcoind_rpc_password=None, rpc_host=None, rpc_port=None,
                 rpc_user=None, rpc_password=None, log_file=None, database_file=None, testnet=False, testcoin=False, unittest=False, headless=False):

    # Unittests always run on testnet.
    if unittest and not testnet:
        raise Exception # TODO

    if not data_dir:
        config.DATA_DIR = appdirs.user_data_dir(appauthor='Counterparty', appname='counterpartyd', roaming=True)
    else:
        config.DATA_DIR = data_dir
    if not os.path.isdir(config.DATA_DIR): os.mkdir(config.DATA_DIR)

    # Configuration file
    configfile = configparser.ConfigParser()
    config_path = os.path.join(config.DATA_DIR, 'counterpartyd.conf')
    configfile.read(config_path)
    has_config = 'Default' in configfile
    #logging.debug("Config file: %s; Exists: %s" % (config_path, "Yes" if has_config else "No"))


    # Bitcoind RPC host
    if bitcoind_rpc_connect:
        config.BITCOIND_RPC_CONNECT = bitcoind_rpc_connect
    elif has_config and 'bitcoind-rpc-connect' in configfile['Default'] and configfile['Default']['bitcoind-rpc-connect']:
        config.BITCOIND_RPC_CONNECT = configfile['Default']['bitcoind-rpc-connect']
    else:
        config.BITCOIND_RPC_CONNECT = 'localhost'

    # Bitcoind RPC port
    if bitcoind_rpc_port:
        config.BITCOIND_RPC_PORT = bitcoind_rpc_port
    elif has_config and 'bitcoind-rpc-port' in configfile['Default'] and configfile['Default']['bitcoind-rpc-port']:
        config.BITCOIND_RPC_PORT = configfile['Default']['bitcoind-rpc-port']
    else:
        config.BITCOIND_RPC_PORT = '8332'
    try:
        int(config.BITCOIND_RPC_PORT)
        assert int(config.BITCOIND_RPC_PORT) > 1 and int(config.BITCOIND_RPC_PORT) < 65535
    except:
        config.BITCOIND_RPC_PORT = '8332'

    # Bitcoind RPC user
    if bitcoind_rpc_user:
        config.BITCOIND_RPC_USER = bitcoind_rpc_user
    elif has_config and 'bitcoind-rpc-user' in configfile['Default'] and configfile['Default']['bitcoind-rpc-user']:
        config.BITCOIND_RPC_USER = configfile['Default']['bitcoind-rpc-user']
    else:
        config.BITCOIND_RPC_USER = 'bitcoinrpc'

    # Bitcoind RPC password
    if bitcoind_rpc_password:
        config.BITCOIND_RPC_PASSWORD = bitcoind_rpc_password
    elif has_config and 'bitcoind-rpc-password' in configfile['Default'] and configfile['Default']['bitcoind-rpc-password']:
        config.BITCOIND_RPC_PASSWORD = configfile['Default']['bitcoind-rpc-password']
    else:
        config.BITCOIND_RPC_PASSWORD = ''

    config.BITCOIND_RPC = 'http://' + config.BITCOIND_RPC_USER + ':' + config.BITCOIND_RPC_PASSWORD + '@' + config.BITCOIND_RPC_CONNECT + ':' + str(config.BITCOIND_RPC_PORT)

    #GUI host:
    if has_config and 'gui-host' in configfile['Default'] and configfile['Default']['gui-host']:
        config.GUI_HOST = configfile['Default']['gui-host']
    else:
        config.GUI_HOST = 'localhost'

    # GUI port
    if has_config and 'gui-port' in configfile['Default'] and configfile['Default']['gui-port']:
        config.GUI_PORT = configfile['Default']['gui-port']
    else:
        config.GUI_PORT = '8080'
    try:
        int(config.GUI_PORT)
        assert int(config.GUI_PORT) > 1 and int(config.GUI_PORT) < 65535
    except:
        config.GUI_PORT = '8080'

    # GUI user
    if has_config and 'gui-user' in configfile['Default'] and configfile['Default']['gui-user']:
        config.GUI_USER = configfile['Default']['gui-user']
    else:
        config.GUI_USER = 'xcpgui'

    # GUI password
    if has_config and 'gui-password' in configfile['Default'] and configfile['Default']['gui-password']:
        config.GUI_PASSWORD = configfile['Default']['gui-password']
    else:
        config.GUI_PASSWORD = ''

    config.GUI_HOME = 'http://' + config.GUI_USER + ':' + config.GUI_PASSWORD + '@' + config.GUI_HOST + ':' + str(config.GUI_PORT)

    config.GUI_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'counterpartygui')

    # Log
    if log_file:
        config.LOG = log_file
    elif has_config and 'logfile' in configfile['Default']:
        config.LOG = configfile['Default']['logfile']
    else:
        config.LOG = os.path.join(config.DATA_DIR, 'counterpartyd.log')

    config.PREFIX = b'CNTRPRTY'

    # Database
    if database_file:
        config.DATABASE = database_file
    else:
        config.DB_VERSION_MAJOR
        config.DATABASE = os.path.join(config.DATA_DIR, 'counterpartyd.' + str(config.DB_VERSION_MAJOR) + '.db')

    config.ADDRESSVERSION = b'\x00'
    config.BLOCK_FIRST = 278270
    config.BURN_START = 278310
    config.BURN_END = 283810
    config.UNSPENDABLE = '1CounterpartyXXXXXXXXXXXXXXXUWLpVr'
            

    # Headless operation
    config.HEADLESS = headless

    
    return configfile

def check_config():
    ok = config.GUI_HOST!=''
    ok = ok and config.GUI_PORT!=''
    ok = ok and config.GUI_USER!=''
    ok = ok and config.GUI_PASSWORD!=''
    ok = ok and config.BITCOIND_RPC_CONNECT!=''
    ok = ok and config.BITCOIND_RPC_PORT!=''
    ok = ok and config.BITCOIND_RPC_USER!=''
    ok = ok and config.BITCOIND_RPC_PASSWORD!=''
    return ok


def connect_to_db(timeout=1000):
    """Connects to the SQLite database, returning a db Connection object"""
    db = apsw.Connection(config.DATABASE)
    cursor = db.cursor()
    cursor.execute('''PRAGMA count_changes = OFF''')
    cursor.close()
    db.setrowtrace(util.rowtracer)
    db.setexectrace(util.exectracer)
    db.setbusytimeout(timeout)
    return db

def init_logging():

    logger = logging.getLogger() #get root logger
    logger.setLevel(logging.INFO)
    #Console logging
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)


def S(value):
    return int(D(value)*config.UNIT)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o,  decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

def check_auth(user, passwd):
    if user==config.GUI_USER and passwd==config.GUI_PASSWORD:
        return True
    return False

def check_bitcoind_for_tx(address, passphrase):
    headers = {'content-type': 'application/json'}
    payload = {
        "method": "dumpprivkey",
        "params": [address],
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = bitcoin.connect(config.BITCOIND_RPC, payload, headers) #TODO: replace by a non blocking connect (no retry)

    if response == None:
        return {'success':False, 'code':-1, 'message':'Cannot communicate with Bitcoind.'}

    if response.status_code not in (200, 500):
        return {'success':False, 'code':-2, 'message':str(response.status_code) + ' ' + response.reason}

    response_json = response.json()

    if 'error' not in response_json.keys() or response_json['error'] == None:
        return {'success':True, 'code':1, 'message':'Bitcoind ready'}
    elif response_json['error']['code'] == -5:   # RPC_INVALID_ADDRESS_OR_KEY
        return {'success':False, 'code':-3, 'message':'Is txindex enabled in Bitcoind?'}
    elif not config.HEADLESS and response_json['error']['code'] == -4:   # Unknown private key (locked wallet?)
        if bitcoin.rpc('validateaddress', [address])['ismine']:
            if passphrase is not None:
                payload['method'] = 'walletpassphrase'
                payload['params'] = [passphrase, 60]
                passhprase_response = bitcoin.connect(config.BITCOIND_RPC, payload, headers)
                passhprase_response_json = passhprase_response.json()
                if 'error' not in passhprase_response_json.keys() or passhprase_response_json['error'] == None:
                    return {'success':True, 'code':1, 'message':'Bitcoind ready'}
                else:
                    return {'success':False, 'code':-7, 'message':'Invalid passhrase'}
            else:
                return {'success':False, 'code':-4, 'message':'Need passhrase'}
        else: 
            return {'success':False, 'code':-5, 'message':'Source address not in wallet.'} 
    else:
        return {'success':False, 'code':-6, 'message':response_json['error']} 



