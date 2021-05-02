import sys
from rdt import RDTSocket

from util import *


def main():
    """Parse command-line argument and call receiver function """
    if len(sys.argv) != 3:
        sys.exit("Usage: python receiver.py [Receiver Port] [Window Size]")
    receiver_port = int(sys.argv[1])
    window_size = int(sys.argv[2])
    r_sock = RDTSocket(window_size)
    r_sock.bind(('127.0.0.1',  receiver_port)) 
    sender_address = r_sock.accept()
    f = open("download.txt", "w")
    msg = r_sock.recv(4096)
    f.write(msg)
    f.close()

if __name__ == "__main__":
    main()
