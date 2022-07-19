#
#    Creates a sender thread, checks if there is a valid key_fob to send every 0.5 seconds
#
#    Copyright (C) 2022 Alfred Daimari
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#

import threading
from time import sleep
import rolling_keyfobs as rkfb


class PuckBitsYdSenderThread(threading.Thread):
    """
    Yardstick sender thread \n
    checks every 0.35s if there is a valid key fob to send
    """

    def __init__(self, id_: str, rkfb_lock: threading.RLock, rolling_kfb: rkfb.RollingKeyFobs) -> None:
        """
        :param id_: name of thread
        :param rkfb_lock: lock for accessing rolling_key_fobs
        :param rolling_kfb: rolling key fob ds
        """
        if not isinstance(rolling_kfb, rkfb.RollingKeyFobs):
            raise TypeError("rolling_kfb is not an instance of RollingKeyFobs")

        t_type = type(threading.RLock())
        if not isinstance(rkfb_lock, t_type):
            raise TypeError("rkfb_lock is not an instance of threading.RLock")

        threading.Thread.__init__(self)
        self.name = id_
        self.lock = rkfb_lock
        self.rolling_kfb = rolling_kfb
        self.shutdown = threading.Event()

    def run(self) -> None:
        while not self.shutdown.is_set():

            self.lock.acquire()
            if self.rolling_kfb.dispatchable:
                self.rolling_kfb.dequeue_send()
            self.lock.release()

            sleep(0.35)

    def shutdown_thread(self):
        """
        terminate the thread
        """
        self.shutdown.set()
