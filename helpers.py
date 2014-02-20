import os
import logging
import json
import configparser
import appdirs
import decimal
import apsw
from counterpartyd.lib import config, util

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

    # testnet
    if testnet:
        config.TESTNET = testnet
    elif has_config and 'testnet' in configfile['Default']:
        config.TESTNET = configfile['Default'].getboolean('testnet')
    else:
        config.TESTNET = False

    # testcoin
    if testcoin:
        config.TESTCOIN = testcoin
    elif has_config and 'testcoin' in configfile['Default']:
        config.TESTCOIN = configfile['Default'].getboolean('testcoin')
    else:
        config.TESTCOIN = False

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
        if config.TESTNET:
            config.BITCOIND_RPC_PORT = '18332'
        else:
            config.BITCOIND_RPC_PORT = '8332'
    try:
        int(config.BITCOIND_RPC_PORT)
        assert int(config.BITCOIND_RPC_PORT) > 1 and int(config.BITCOIND_RPC_PORT) < 65535
    except:
        raise Exception("Please specific a valid port number bitcoind-rpc-port configuration parameter")

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
        raise exceptions.ConfigurationError('bitcoind RPC password not set. (Use configuration file or --bitcoind-rpc-password=PASSWORD)')

    config.BITCOIND_RPC = 'http://' + config.BITCOIND_RPC_USER + ':' + config.BITCOIND_RPC_PASSWORD + '@' + config.BITCOIND_RPC_CONNECT + ':' + str(config.BITCOIND_RPC_PORT)

    # RPC host
    if rpc_host:
        config.RPC_HOST = rpc_host
    elif has_config and 'rpc-host' in configfile['Default'] and configfile['Default']['rpc-host']:
        config.RPC_HOST = configfile['Default']['rpc-host']
    else:
        config.RPC_HOST = 'localhost'

    # RPC port
    if rpc_port:
        config.RPC_PORT = rpc_port
    elif has_config and 'rpc-port' in configfile['Default'] and configfile['Default']['rpc-port']:
        config.RPC_PORT = configfile['Default']['rpc-port']
    else:
        if config.TESTNET:
            config.RPC_PORT = '14000'
        else:
            config.RPC_PORT = '4000'
    try:
        int(config.RPC_PORT)
        assert int(config.RPC_PORT) > 1 and int(config.RPC_PORT) < 65535
    except:
        raise Exception("Please specific a valid port number rpc-port configuration parameter")

    # RPC user
    if rpc_user:
        config.RPC_USER = rpc_user
    elif has_config and 'rpc-user' in configfile['Default'] and configfile['Default']['rpc-user']:
        config.RPC_USER = configfile['Default']['rpc-user']
    else:
        config.RPC_USER = 'rpc'

    # RPC password
    if rpc_password:
        config.RPC_PASSWORD = rpc_password
    elif has_config and 'rpc-password' in configfile['Default'] and configfile['Default']['rpc-password']:
        config.RPC_PASSWORD = configfile['Default']['rpc-password']
    else:
        raise exceptions.ConfigurationError('RPC password not set. (Use configuration file or --rpc-password=PASSWORD)')

    # Log
    if log_file:
        config.LOG = log_file
    elif has_config and 'logfile' in configfile['Default']:
        config.LOG = configfile['Default']['logfile']
    else:
        if config.TESTNET:
            config.LOG = os.path.join(config.DATA_DIR, 'counterpartyd.testnet.log')
        else:
            config.LOG = os.path.join(config.DATA_DIR, 'counterpartyd.log')

    if not unittest:
        if config.TESTCOIN:
            config.PREFIX = b'XX'                   # 2 bytes (possibly accidentally created)
        else:
            config.PREFIX = b'CNTRPRTY'             # 8 bytes
    else:
        config.PREFIX = config.UNITTEST_PREFIX

    # Database
    if config.TESTNET:
        config.DB_VERSION_MAJOR = str(config.DB_VERSION_MAJOR) + '.testnet'
    if database_file:
        config.DATABASE = database_file
    else:
        config.DB_VERSION_MAJOR
        config.DATABASE = os.path.join(config.DATA_DIR, 'counterpartyd.' + str(config.DB_VERSION_MAJOR) + '.db')

    # (more) Testnet
    if config.TESTNET:
        if config.TESTCOIN:
            config.ADDRESSVERSION = b'\x6f'
            config.BLOCK_FIRST = 154908
            config.BURN_START = 154908
            config.BURN_END = 4017708   # Fifty years, at ten minutes per block.
            config.UNSPENDABLE = 'mvCounterpartyXXXXXXXXXXXXXXW24Hef'
        else:
            config.ADDRESSVERSION = b'\x6f'
            config.BLOCK_FIRST = 154908
            config.BURN_START = 154908
            config.BURN_END = 4017708   # Fifty years, at ten minutes per block.
            config.UNSPENDABLE = 'mvCounterpartyXXXXXXXXXXXXXXW24Hef'
    else:
        if config.TESTCOIN:
            config.ADDRESSVERSION = b'\x00'
            config.BLOCK_FIRST = 278270
            config.BURN_START = 278310
            config.BURN_END = 2500000   # A long time.
            config.UNSPENDABLE = '1CounterpartyXXXXXXXXXXXXXXXUWLpVr'
        else:
            config.ADDRESSVERSION = b'\x00'
            config.BLOCK_FIRST = 278270
            config.BURN_START = 278310
            config.BURN_END = 283810
            config.UNSPENDABLE = '1CounterpartyXXXXXXXXXXXXXXXUWLpVr'

    # Headless operation
    config.HEADLESS = headless

    #GUI host:
    if has_config and 'gui-host' in configfile['Default'] and configfile['Default']['gui-host']:
        config.GUI_HOST = configfile['Default']['gui-host']
    else:
        config.GUI_HOST = config.RPC_HOST

    # GUI port
    if has_config and 'gui-port' in configfile['Default'] and configfile['Default']['gui-port']:
        config.GUI_PORT = configfile['Default']['gui-port']
    else:
        config.GUI_PORT = 8080

    # GUI user
    if has_config and 'gui-user' in configfile['Default'] and configfile['Default']['gui-user']:
        config.GUI_USER = configfile['Default']['gui-user']
    else:
        config.GUI_USER = config.RPC_USER

    # GUI password
    if has_config and 'gui-password' in configfile['Default'] and configfile['Default']['gui-password']:
        config.GUI_PASSWORD = configfile['Default']['gui-password']
    else:
        config.GUI_PASSWORD = config.RPC_PASSWORD

    config.GUI_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'counterpartygui')
    return configfile


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

