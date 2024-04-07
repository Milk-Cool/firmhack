import json
import subprocess
import logging
import time
import os


logger = logging.getLogger(__name__)


class HostapdManaNetworkType:
    NORMAL: int = 0
    ENTERPRISE: int = 1


class GeneralConfig:
    hostapdmanacmd: str = "hostapd-mana"
    proxychainscmd: str = "proxychains"
    dnsmasqcmd: str = "dnsmasq"
    nm: bool = True
    inetinterface: str = ""


class APConfig:
    interface: str = "wlan0"
    loud: bool = True
    nettype: HostapdManaNetworkType = HostapdManaNetworkType.NORMAL
    name: str = "My WiFi"
    password: str = "mypasswd"


class ProxyConfig:
    logfile: str = "firmhack.log"
    burp: int = 0


class AddressConfig:
    address: str = "http://firmhack"
    file: str = "example/browser-detect.html"
    headers: dict = {}


class Config:
    general: GeneralConfig = GeneralConfig()
    ap: APConfig = APConfig()
    proxy: ProxyConfig = ProxyConfig()
    addresses: AddressConfig = [AddressConfig()]


def get_hostapd_mana_type(type: str) -> HostapdManaNetworkType:
    return HostapdManaNetworkType.ENTERPRISE if type == "enterprise" else HostapdManaNetworkType.NORMAL


def form_hostapd_mana_config(interace: str, loud: bool, type: HostapdManaNetworkType, name: str, password: str) -> None:
    config = f"""# generated by firmhack
interface={interace}
ssid={name}
channel=6
hw_mode=g
"""
    if type == HostapdManaNetworkType.ENTERPRISE:
        # TODO: enterprise networks support
        config += f"""enable_sycophant=1
sycophant_dir=/tmp/
"""
    if password and type != HostapdManaNetworkType.ENTERPRISE:
        config += f"""ieee80211n=1
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
wpa_passphrase={password}
auth_algs=3
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP CCMP
"""
    return config


def get_config() -> dict:
    f = open("firmhack.json")
    config = json.loads(f.read())
    f.close()
    return config


def dict_to_obj_config(dict_config: dict) -> Config:
    general_config = GeneralConfig()
    general_config.hostapdmanacmd = dict_config["general"]["hostapdmanacmd"]
    general_config.proxychainscmd = dict_config["general"]["proxychainscmd"]
    general_config.dnsmasqcmd = dict_config["general"]["dnsmasqcmd"]
    general_config.nm = dict_config["general"]["nm"]
    general_config.inetinterface = dict_config["general"]["inetinterface"]

    ap_config = APConfig()
    ap_config.interface = dict_config["ap"]["interface"]
    ap_config.loud = dict_config["ap"]["loud"]
    ap_config.nettype = get_hostapd_mana_type(dict_config["ap"]["type"])
    ap_config.name = dict_config["ap"]["name"]
    ap_config.password = dict_config["ap"]["password"]

    proxy_config = ProxyConfig()
    proxy_config.logfile = dict_config["proxy"]["logfile"]
    proxy_config.burp = dict_config["proxy"]["burp"]

    addresses_config: list[AddressConfig] = []
    for address in dict_config["addresses"]:
        address_config = AddressConfig()
        address_config.address = address["address"]
        address_config.file = address["file"]
        address_config.headers = address["headers"]
        addresses_config.append(address_config)

    config = Config()
    config.general = general_config
    config.ap = ap_config
    config.proxy = proxy_config
    config.addresses = addresses_config
    return config


def form_proxychains_config(port: int | str) -> str:
    return f"""[ProxyList]
http 127.0.0.1 {port}"""


def form_dnsmasq_config(interface: str) -> str:
    return f"""interface={interface}
bind-interfaces
dhcp-range=10.0.0.10,10.0.0.250,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
listen-address=127.0.0.1"""


def reset_console() -> None:
    subprocess.run(["stty", "sane"])


def main() -> None:
    logging.basicConfig(filename="firmhack.log",
                        level=logging.INFO, filemode="w")
    dict_config = get_config()
    config = dict_to_obj_config(dict_config)
    logger.info("Config seems to be valid!")
    hostapd_mana_config = form_hostapd_mana_config(
        config.ap.interface, config.ap.loud, config.ap.nettype, config.ap.name, config.ap.password)
    logger.info("Generated hostapd-mana config!")
    hostapd_mana_config_f = open("hostapd.conf", "w")
    hostapd_mana_config_f.write(hostapd_mana_config)
    hostapd_mana_config_f.close()
    logger.info("Saved hostapd-mana config!")
    dnsmasq_config = form_dnsmasq_config(config.ap.interface)
    logger.info("Generated dnsmasq config!")
    dnsmasq_config_f = open("dnsmasq.conf", "w")
    dnsmasq_config_f.write(dnsmasq_config)
    dnsmasq_config_f.close()
    logger.info("Saved dnsmasq config!")
    if config.proxy.burp == 0:
        pass  # TODO: start proxy
    proxychains_config = form_proxychains_config(
        1337 if config.proxy.burp == 0 else config.proxy.burp)
    logger.info("Generated proxychains config!")
    proxychains_config_f = open("proxychains.conf", "w")
    proxychains_config_f.write(proxychains_config)
    proxychains_config_f.close()
    logger.info("Saved proxychains config!")
    if config.general.nm:
        logger.info("Disabling NetworkManager...")
        subprocess.run(["sudo", "nmcli", "radio", "wifi", "off"])
    # logger.info("Disabling interface...")
    # subprocess.run(["sudo", "ifconfig", config.ap.interface, "down"])
    logger.info("Setting things up before starting the AP...")
    dnsmasq = subprocess.Popen(
        ["sudo", config.general.dnsmasqcmd, "-C", "dnsmasq.conf", "-d"])
    subprocess.run(["sudo", "ifconfig", config.ap.interface,
                   "10.0.0.1", "netmask", "255.255.255.0", "up"])
    if config.general.inetinterface:
        subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING",
                       "-o", config.general.inetinterface, "-j", "MASQUERADE"])
        subprocess.run(["sudo", "iptables", "-A", "FORWARD", "-i",
                       config.ap.interface, "-o", config.general.inetinterface, "-j", "ACCEPT"])
        subprocess.run(["sudo", "iptables", "-A", "FORWARD", "-i", config.general.inetinterface, "-o",
                       config.ap.interface, "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])
    reset_console()
    logger.info("Starting hostapd-mana with proxychains...")
    proxychains_and_hostapd = subprocess.Popen(
        ["sudo", config.general.proxychainscmd, "-f", "proxychains.conf", config.general.hostapdmanacmd, "hostapd.conf"])
    reset_console()
    try:
        proxychains_and_hostapd.wait()
    except KeyboardInterrupt:
        pass
    dnsmasq.terminate()
    if config.general.nm:
        logger.info("hostapd-mana has stopped. Enabling NetworkManager...")
        subprocess.run(["sudo", "nmcli", "radio", "wifi", "on"])
    reset_console()


if __name__ == "__main__":
    main()
