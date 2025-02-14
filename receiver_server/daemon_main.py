import daemon
from main import main as receiver_main
import logging
log = logging.getLogger(__name__)

def main():
    try:
        with daemon.DaemonContext():
            receiver_main()
    except Exception as e:
        log.exception(f"Exception in daemon: {str(e)}")

if __name__ == '__main__':
    main()