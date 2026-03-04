DHCP_SERVER_IP = "127.0.0.1"
DHCP_SERVER_PORT = 6767

LEASE_TIME = 120  # seconds

IP_POOL = [f"10.0.0.{i}" for i in range(2, 21)]

DNS_LOCAL_IP = "127.0.0.1"
DNS_LOCAL_PORT = 5358
GOOGLE_DNS = ("8.8.8.8", 53)
BUFFER_SIZE = 1024

APP_SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345

OFFER_TTL = 15  # seconds (pending offer expiration)