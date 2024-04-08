# Requirements

[`hostapd-mana`](https://github.com/sensepost/hostapd-mana), [Python 3](https://www.python.org/), [dnsmasq](https://wiki.debian.org/dnsmasq), `requirements.txt` packages

# Config explanation in detial
The config is a JSON file called `firmhack.json`.
## `general`
General settings.
### `hostapdmanacmd`
Command used to invoke hostapd-mana. Either the path to your `hostapd-mana` file or the command name if it's already in PATH.
### `dnsmasqcmd`
Command used to invoke dnsmasq. It's usually in PATH, so the recommended value is `dnsmasq`.
### `mitmdumpcmd`
Command used to invoke mitmdump. It's usually in PATH, so the recommended value is `mitmdump`.
### `nm`
Whether to disable NetworkManager while `hostapd-mana` is running.\
If you use this setting, you should only press ^C **ONLY ONCE** when stopping hostapd-mana.
### `inetinterface`
The interface to use to access internet from the connected devices.\
Usually something like `wlan0` or `wlp1s0`.\
Leave this blank if no internet is required.
## `ap`
Access point settings.
### `interface`
The network interface to use with hostapd-mana. Usually something like `wlan0` or `wlp1s0`.
### `loud`
Determines whether hostapd-mana should advertize the network to all devices rather than just those that are seeking for the network.
### `type`
`normal` for WPA/WPA2-Personal networks and `enterprise` for WPA2-Enterprise networks. Set this to `enterprise` if your network requires both a username and a password.
### `password`
The WiFi password for `normal` networks. Unused with `enterprise` networks.
### `name`
The Wi-Fi network name. Set this to the name of the network your target device is connected to.
## `proxy`
Proxy settings.
### `logfile`
The name of the file to log intercepted request paths to. Unused if `burp` is set to `true`.
### `burp`
If you're using Burp Suite as a proxy, set this to the proxy port (`8080` by default iirc). This should also work with other custom proxies. If you're using the firmhack proxy, leave this set to `0`.
### `hosts`
Ignored hosts regex, like `^(?!example\\.com:)`. See mitmproxy's [`--ignore-hosts`](https://docs.mitmproxy.org/stable/howto-ignoredomains/) option.
## `addresses`
A set of adresses settings. (JSON array, see `firmhack.example.json`)
### `address`
The URL address to intercept.
### `file`
The path of the file to serve.
### `headers`
The headers object. See example.