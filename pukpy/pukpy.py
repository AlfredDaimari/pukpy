#!/usr/bin/python3.8

import threading
import signal
import argparse

from time import sleep
import rolling_keyfobs as rkfb
from puck_receiver import PuckReceiverThread
from puck_sender import PuckBitsYdSenderThread
from errors.service_exit import ServiceExit


def sigint_handler(signal_, frame):
    print("received sigint, exiting gracefully")
    raise ServiceExit


def args_handler() -> argparse.Namespace:
    """
    :return: arguments from the terminal
    """
    # TODO: add more configs (jamming configs, sending configs, etc)
    parser = argparse.ArgumentParser("yd_stick configuration")
    parser.add_argument('--nyd', help='prevent use of yd_stick', action='store_false')
    args = parser.parse_args()
    return args


def main() -> None:
    signal.signal(signal.SIGINT, sigint_handler)
    args = args_handler()
    rolling_kfb = rkfb.RollingKeyFobs(yd_bool=args.nyd)
    rkfb_lock = threading.RLock()

    try:
        thread1 = PuckReceiverThread("thread1", rkfb_lock, rolling_kfb)
        thread2 = PuckBitsYdSenderThread("thread2", rkfb_lock, rolling_kfb)
        thread1.start()
        thread2.start()

        while True:
            sleep(0.5)

    except ServiceExit:

        # wait for both to end
        thread1.shutdown_thread()
        thread2.shutdown_thread()

        thread1.join()
        thread2.join()


main()
