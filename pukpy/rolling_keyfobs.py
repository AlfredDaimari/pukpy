from time import time_ns as tns
from typing import List
from termcolor import cprint
from rflib import *
from ydstick import YdStick, YdSendingEvent
from cars.maruti import MarutiNipponKeyFobPacket
from cars.toyota import InnovaKeyFobPacket
from cars.keyfob import KeyFobPacket

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

    def __init__(self, yd_bool: bool) -> None:
        self.rolling_kfb_list = []

        self.yd_stick = YdStick(init=yd_bool)
        self.__yd_sending = YdSendingEvent()
        print("the yardstick has been initialized")

    def __len__(self) -> int:
        return len(self.rolling_kfb_list)

    def __str__(self) -> str:
        str_ = ""
        for kfb_list in self.rolling_kfb_list:
            for kfb in kfb_list:
                str_ += str(kfb)
            str_ += "\n--  next key fob --  \n"
        return str_

    def __shift(self) -> List[KeyFobPacket]:
        """
        dequeue the first element from key fob
        """
        return self.rolling_kfb_list.pop(0)

    def __create_tmp_kfb_list(self, kfb_bb: List[str], kfb_type: str, bpk_recv_time: int) \
            -> List[KeyFobPacket]:
        """
        :param kfb_bb: in form [100001:1, 10000:23]
        :param kfb_type: key fob type
        :param bpk_recv_time: time received
        :return: List[KeyFobPacket]
        """
        flt_kfb_bb_list = CAR_FOBS[kfb_type].filter(kfb_bb)
        kfb_list = []
        for kfb in flt_kfb_bb_list:
            kfb_list.append(CAR_FOBS[kfb_type](kfb, kfb_type, bpk_recv_time))
        return kfb_list

    def __get_rolling_kfb_type(self) -> str:
        """
        :return: type of key fobs inside rolling key fob ds
        """
        return self.rolling_kfb_list[-1][-1].kfb_type

    @property
    def sending(self) -> bool:
        """
        is yd_stick sending or not
        :return: True or False
        """
        return self.__yd_sending.is_set()

    def get_lst_kfb_recv_time(self) -> int:
        """
        :return: receiving time in unix ns of last rolling key_fob_packet
        """
        return self.rolling_kfb_list[-1][-1].bpk_recv_time

    def pp_print(self, index) -> None:
        """
        printing for debugging
        :param index: the key fob to print from
        """
        for key_fob in self.rolling_kfb_list[index]:
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
            lst_kfb_list_time = self.get_lst_kfb_recv_time()
            if (cur_time - lst_kfb_list_time) > 800000000:
                return True

        return False

    def dequeue_send(self) -> None:
        """
        send the first message in the queue
        """
        cprint("key fobs to be sent", "yellow")
        self.pp_print(0)
        kfbs_to_be_sent = self.__shift()
        print("\n")  # new line

        rf_kfb = self.yd_stick.create_rf_kfbs(kfbs_to_be_sent)

        # stop jamming -> start sending -> stop sending -> begin jamming
        self.yd_stick.stop_jamming()
        self.__yd_sending.set_sending()
        rf_kfb.send()
        self.__yd_sending.unset_sending()
        self.yd_stick.begin_jamming()

        cprint("current rolling key_fobs struct", "yellow")
        self.pp_print_all()

    def push(self, kfb_bb: List[str], kfb_type: str) -> None:
        """
        add a new key fob to list or concatenate with previous key fob \n
        :param kfb_bb: a list in the form ["bits:gap", "bits:gap"]
        :param kfb_type: type of key fob
        :return None
        """

        if len(kfb_bb) < 1:
            cprint("key fob packet is not valid. dropping key fob packet", "white", "on_red")

        cur_time = tns()
        tmp_kfb_list = self.__create_tmp_kfb_list(kfb_bb, kfb_type, cur_time)

        if len(self.rolling_kfb_list) == 0:
            self.rolling_kfb_list = [tmp_kfb_list]
            cprint(f"first key fob packet received of type {kfb_type}", "white", "on_yellow")
        else:
            if self.__get_rolling_kfb_type() != kfb_type:
                cprint("key fob packet is not the same type as previous. dropping key fob packet", "white", "on_red")

            elif (cur_time - self.get_lst_kfb_recv_time()) < 1000000000:
                self.rolling_kfb_list[-1] += tmp_kfb_list
                cprint("appending to previous packet", "white", "on_yellow")

            else:
                self.rolling_kfb_list.append(tmp_kfb_list)
                cprint("new key fob packet received", "white", "on_yellow")
