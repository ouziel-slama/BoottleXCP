counterpartyws
==========

A simple webserver + HTML GUI for Counterparty

# Requirement

* you must have bitcoind running with txindex=1 and server=1 in config file. 


# Quick install and run 
<b>(thanks to romerun)</b>

<pre>
brew update
brew install sqlite

pip3 install bottle appdirs==1.2.0 prettytable==0.7.2 python-dateutil==2.2 requests==2.1.0 cherrypy==3.2.4 json-rpc==1.1 pycoin==0.25 pytest==2.5.1
pip3 install https://github.com/rogerbinns/apsw/archive/master.zip

git clone --recursive https://github.com/JahPowerBit/BoottleXCP.git

python3 boottlexcp.py

</pre>

* "START PARTY!" to start blocks following and web server.
* "OPEN WALLET" top open the GUI
* "QUIT" to stop blocks following and web server and close manager
* "CONFIG" to change configuration

![ScreenShot](http://i.imgur.com/hcqWHnL.png)

![ScreenShot](http://i.imgur.com/t9loYX3.png)

![ScreenShot](http://i.imgur.com/5AhiSdO.png)

# Configuration file

OS  | Path
------------- | -------------
MacOS | ~/Library/Application Support/counterpartyd/counterpartyd.conf
XP | C:\Documents and Settings\username\Application Data\counterpartyd\counterpartyd.conf
Vista, 7 | C:\Users\username\AppData\Roaming\counterpartyd\counterpartyd.conf
Linux | ~/.config/counterpartyd/counterpartyd.conf

<pre>
[Default]
bitcoind-rpc-connect=192.168.2.254
bitcoind-rpc-port=8332
bitcoind-rpc-user=xxxxx
bitcoind-rpc-password=xxxxx
rpc-password=xxxxx

gui-host=localhost
gui-port=8080
gui-user=xxxxx
gui-password=xxxxx
</pre>
