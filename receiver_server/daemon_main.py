import daemon
from main import main
import logging
log = logging.getLogger(__name__)

try:
    with daemon.DaemonContext():
        main()
except Exception as e:
    log.exception(f"Exception in daemon: {str(e)}")
