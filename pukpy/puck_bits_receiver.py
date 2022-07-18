#
#    Creates a dbus service, used to read rf bits sent from rtl_433
#     
#    Copyright (C) 2022 Alfred Daimari 
#    
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
import threading
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from datetime import datetime
from termcolor import cprint
from rolling_keyfobs import RollingKeyFobs
from rf import YDSendPacketEvent

OPATH = "/org/autosec/PuckBitsReceiver"
IFACE = "org.autosec.PuckBitsReceiverInterface"
BUS_NAME = "org.autosec.PuckBitsReceiver"


class PuckBitsReceiver(dbus.service.Object):
    """
    For creating a rf bits listener service on dbus
    """

    def __init__(self, lock: threading.RLock, rolling_key_fobs: RollingKeyFobs, yd_sending: YDSendPacketEvent) -> None:
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        bus.request_name(BUS_NAME)
        bus_name = dbus.service.BusName(BUS_NAME, bus=bus)
        dbus.service.Object.__init__(self, bus_name, OPATH)
        print("the dbus has been initialized")

        self.lock = lock
        self.rolling_key_fobs = rolling_key_fobs
        self.yd_sending = yd_sending

    @dbus.service.method(dbus_interface=IFACE, in_signature="s", out_signature="s", sender_keyword="sender",
                         connection_keyword="conn")
    def ReceiveBits(self, bits: str, sender=None, conn=None):
        """
        receiver function for bits
        """
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S %d/%m/%Y")
        cprint(f"received: {bits} at {dt_string}", "white", "on_yellow")

        # only push bits when yard stick is not sending, else we may capture the sent-out bits
        if not self.yd_sending.is_set():
            self.lock.acquire()
            self.rolling_key_fobs.push(bits.split('-'))
            self.lock.release()
        else:
            cprint("received packets while yd_stick was sending, dropping erroneous packets", "white", "on_red")

        return "saibo"


class PuckBitsReceiverThread(threading.Thread):
    """
    Puck bits receiver thread,
    received bit packets and stores it withing rolling key fobs
    """

    def __init__(self, name: str, lock: threading.RLock, rolling_key_fobs: RollingKeyFobs,
                 yd_sending: YDSendPacketEvent) -> None:
        threading.Thread.__init__(self)

        t_type = type(threading.RLock())
        if not isinstance(lock, t_type):
            raise TypeError("lock is not an instance of threading.RLock")

        if not isinstance(rolling_key_fobs, RollingKeyFobs):
            raise TypeError("rolling_key_fobs is not an instance of RollingKeyFobs")

        if not isinstance(yd_sending, YDSendPacketEvent):
            raise TypeError("yd_sending is not an instance of YDSendPacketEvent")

        self.name = name
        self.lock = lock
        self.rolling_key_fobs = rolling_key_fobs
        self.mainloop = GLib.MainLoop()
        self.yd_sending = yd_sending

    def run(self) -> None:
        puck_bits_receiver = PuckBitsReceiver(self.lock, self.rolling_key_fobs, self.yd_sending)
        self.mainloop.run()

    def shutdown_thread(self):
        """
        shutdown the thread
        """
        self.mainloop.quit()
