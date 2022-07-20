#!/usr/bin/python3
import dbus
import signal
import json
from termcolor import cprint


# TODO: send key fob sent from pukpy

def sigint_handler(sigal_, frame):
    print("signal caught! Exiting gracefully!")
    exit(0)


def view_rkfb(msg: str) -> None:
    """
    Pretty printer for view_rkfb
    :param msg: msg received from pukpy through dbus
    :return: None
    """
    rkfb = json.loads(msg)
    for i in range(len(rkfb)):

        cprint(f"\n\nkey fob {i + 1}", "yellow")
        kfb_list = rkfb[i]

        for j in range(len(kfb_list)):
            cprint(f"\n-- kfb in index {j + 1} --")
            kfb = kfb_list[j]

            for r in range(len(kfb)):
                rs = kfb[r].split(":")
                cprint(f"{rs[0]} - {rs[1]} --- {r + 1}", "green")


def main():
    signal.signal(signal.SIGINT, sigint_handler)
    bus = dbus.SystemBus()
    puck_receiver = bus.get_object('org.autosec.PuckReceiver', '/org/autosec/PuckReceiver')
    puck_receiver_iface = dbus.Interface(puck_receiver, "org.autosec.PuckReceiverInterface")

    while True:
        com = input("> ")
        msg = puck_receiver_iface.ExecuteCommand(com)

        if com == "view-rkfb":
            view_rkfb(msg)
        elif com == "send-rkfb":
            print(msg)
        else:
            print(msg)


main()
