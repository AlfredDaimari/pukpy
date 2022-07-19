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
import rolling_keyfobs as rkfb

OPATH = "/org/autosec/PuckReceiver"
IFACE = "org.autosec.PuckReceiverInterface"
BUS_NAME = "org.autosec.PuckReceiver"


class PuckReceiver(dbus.service.Object):
    """
    creating a rf bits listener, puck command listener service on dbus
    """

    def __init__(self, rkfb_lock: threading.RLock, rolling_kfb: rkfb.RollingKeyFobs) -> None:
        """
        :param rkfb_lock: rolling key fob lock
        :param rolling_kfb: instance of rolling key fobs ds
        """
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        bus.request_name(BUS_NAME)
        bus_name = dbus.service.BusName(BUS_NAME, bus=bus)
        dbus.service.Object.__init__(self, bus_name, OPATH)
        print("the dbus has been initialized")

        self.rkfb_lock = rkfb_lock
        self.rolling_kfb = rolling_kfb

    @dbus.service.method(dbus_interface=IFACE, in_signature="s", out_signature="s", sender_keyword="sender",
                         connection_keyword="conn")
    def ReceiveBits(self, bits: str, sender=None, conn=None):
        """
        receiver function for bits
        """
        now = datetime.now()
        dt_string = now.strftime("%H:%M:%S %d/%m/%Y")
        cprint(f"received: {bits} at {dt_string}", "white")

        # only push bits when yard stick is not sending ( we may capture our own sent-out bits )
        if not self.rolling_kfb.is_sending:
            self.rkfb_lock.acquire()

            bits_spl = bits.split('-')
            kfb_type = bits_spl[-1]
            kfb_bb = bits_spl[:-1]
            self.rolling_kfb.push(kfb_bb, kfb_type)

            self.rkfb_lock.release()
        else:
            cprint("received packets while yd_stick was sending, dropping erroneous packets", "white", "on_red")

        return "saibo"

    @dbus.service.method(dbus_interface=IFACE, in_signature='s', out_signature='s', sender_keyword="sender",
                         connection_keyword="conn")
    def ExecuteCommand(self, com: str, sender=None, conn=None):
        """
        receiver function for commands
        """
        msg = 'error: no such command'

        if com == "view-rkfb":
            self.rkfb_lock.acquire()
            msg = self.rolling_kfb.to_json()
            self.rkfb_lock.release()

        return msg


class PuckReceiverThread(threading.Thread):
    """
    Puck bits receiver thread,
    received bit packets and stores it withing rolling key fobs
    """

    def __init__(self, id_: str, rkfb_lock: threading.RLock, rolling_kfb: rkfb.RollingKeyFobs) -> None:
        """
        :param id_: name of thread
        :param rkfb_lock: rolling key fob lock
        :param rolling_kfb: instance of rolling key fobs ds
        """
        threading.Thread.__init__(self)

        t_type = type(threading.RLock())
        if not isinstance(rkfb_lock, t_type):
            raise TypeError("rkfb_lock is not an instance of threading.RLock")

        if not isinstance(rolling_kfb, rkfb.RollingKeyFobs):
            raise TypeError("rolling_kfb is not an instance of RollingKeyFobs")

        self.name = id_
        self.rkfb_lock = rkfb_lock
        self.rolling_kfb = rolling_kfb
        self.mainloop = GLib.MainLoop()

    def run(self) -> None:
        puck_receiver = PuckReceiver(self.rkfb_lock, self.rolling_kfb)
        self.mainloop.run()

    def shutdown_thread(self):
        """
        shutdown the thread
        """
        self.mainloop.quit()
