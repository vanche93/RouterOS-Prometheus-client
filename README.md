# RouterOS Prometheus client
#### Description

Prometheus client for Mikrotik devices. Can be configured to collect metrics
from a single device or multiple devices.

To access the api, use [RouterOS-api](https://github.com/socialwifi/RouterOS-api).

To create metrics, use [Prometheus Python Client](https://github.com/prometheus/client_python).

## Install
`pip install routeros-prometheus-client`

## Usage

#### Mikrotik Config

Create a user on the device that has API and read-only access.

`/user group add name=prometheus policy=api,read,winbox`

Create the user to access the API via.

`/user add name=prometheus group=prometheus password=changeme`

#### Create config file

```
[my_router]
host = 192.168.1.1
username = login
password = password
plaintext_login = True
interface = True
wireless = False
caps_man = True
l2tp = True
gre = True

[my_second_router]
host = 192.168.1.2
username = login
password = password
plaintext_login = True
interface = True
wireless = True
caps_man = False
l2tp = False
gre = False
```
* `[section]` - String - Used for identification device
* `host` - String - Hostname or IP of device
* `username` - String - Login username - Default 'admin'
* `password` - String - Login password - Default empty string
* `port` - Integer - TCP Port for API - Default 8728 or 8729 when using SSL
* `plaintext_login` - Boolean - Try plaintext login (for RouterOS 6.43 onwards) - Default False
* `use_ssl` - Boolean - Use SSL or not? - Default False
* `ssl_verify` - Boolean - Verify the SSL certificate? - Default True
* `ssl_verify_hostname` - Boolean - Verify the SSL certificate hostname matches? - Default True
* `ssl_context` - Object - Pass in a custom SSL context object. Overrides other options. - Default None
* `interface` `wireless` `caps_man` `l2tp` `gre` - What metrics to collect

#### Start routeros-prometheus-client
`routeros-prometheus-client -c routeros-prometheus-client\config.ini -p 8000`

* `-c` `--config` path to `config.ini`
* `-p` `--port` HTTPServer port
