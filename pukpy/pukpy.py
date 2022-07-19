#!/usr/bin/python3.8

import threading
import signal
from time import sleep
from rolling_keyfobs import RollingKeyFobs
from puck_bits_receiver import PuckReceiverThread
from puck_bits_sender import PuckBitsYdSenderThread
from errors.service_exit import ServiceExit


def sigint_handler(signal_, frame):
    print("received sigint, exiting gracefully")
    raise ServiceExit


def main() -> None:
    signal.signal(signal.SIGINT, sigint_handler)

    rolling_kfb = RollingKeyFobs()
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
