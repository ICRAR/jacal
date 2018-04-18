import logging
from jacalingest.testbed.icerunner import IceRunner

def main():
    logging.basicConfig(level=logging.INFO, format='%(threadName)s, %(module)s: %(message)s')

    icerunner = IceRunner("testbed_data")
    icerunner.start()

if __name__ == "__main__":
    main()

