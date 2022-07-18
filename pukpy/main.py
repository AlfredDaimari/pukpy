#!/usr/bin/python3.8

import threading
import signal
from time import sleep
from rf import YDSendPacketEvent
from rolling_keyfobs import RollingKeyFobs
from puck_bits_receiver import PuckBitsReceiverThread
from puck_bits_sender import PuckBitsYdSenderThread
from service_exit import ServiceExit


def sigint_handler(signal_, frame):
    print("received sigint, exiting gracefully")
    raise ServiceExit


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)

    rolling_key_fobs = RollingKeyFobs()
    lock = threading.RLock()

    try:
        yd_sending = YDSendPacketEvent()
        thread1 = PuckBitsReceiverThread("thread1", lock, rolling_key_fobs, yd_sending)
        thread2 = PuckBitsYdSenderThread("thread2", lock, rolling_key_fobs, yd_sending)
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
