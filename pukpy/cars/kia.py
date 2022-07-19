from typing import List
from keyfob import KeyFobPacket
from ..ydstick import YdStickConfig


class KiaCarrenceKeyFobPacket(KeyFobPacket):
    """
    data structure to hold maruti nippon key fob
    """

    def __init__(self, kfb_list: List[str], kfb_type: str, bpk_recv_time: int) -> None:
        cfg = YdStickConfig()
        KeyFobPacket.__init__(self, cfg, kfb_list, kfb_type, bpk_recv_time)
        self.__clean()

    def __clean(self):
        """
        cleans up the bpk for maruti
        :return: None
        """
        self.bpk_list[0].bpk_drop(371)
        self.bpk_list[0].bpk_pad(1)

    @classmethod
    def filter(cls, kfb_bb: List[str]) -> List[List[str]]:
        # TODO: add more filters
        kfb_list = []
        for i in range(1, len(kfb_bb), 2):
            kfb_list.append([kfb_bb[i - 1], kfb_bb[i]])
        return kfb_list

    def concat_bpk_list(self) -> str:
        str_ = "0" * 8 + "10" * 238 + "1"
        str_ += ":" + "0.072" + ":"
        str_ += self.bpk_list[0].bpk
        return str_