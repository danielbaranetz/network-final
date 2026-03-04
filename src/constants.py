DHCP_SERVER_IP = "127.0.0.1"
DHCP_SERVER_PORT = 6767

LEASE_TIME = 120  # seconds

IP_POOL = [f"10.0.0.{i}" for i in range(2, 21)]

DNS_SERVER_IP = "127.0.0.1"
APP_SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345

OFFER_TTL = 15  # seconds (pending offer expiration)