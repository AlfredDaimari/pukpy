from typing import List
from .keyfob import KeyFobPacket
from .yd_config import YdStickConfig


class InnovaKeyFobPacket(KeyFobPacket):
    """
    data structure to hold toyota innova crysta key fob
    """

    def __init__(self, kfb_list: List[str], kfb_type: str, bpk_recv_time: int) -> None:
        cfg = YdStickConfig()
        KeyFobPacket.__init__(self, cfg, kfb_list, kfb_type, bpk_recv_time)
        self.__clean()

    def __clean(self):
        """
        cleans up the bpk for toyota
        :return: None
        """
        if len(self.bpk_list[0]) > 236:
            self.bpk_list[0].bpk_drop(237)
            self.bpk_list[0].bpk_pad(3)

    @classmethod
    def filter(cls, kfb_bb: List[str]) -> List[List[str]]:
        kfb_bb_list = []
        for kfb_row in kfb_bb:
            if len(kfb_row.split(":")[0]) >= 236:
                kfb_bb_list.append([kfb_row])
        return kfb_bb_list

    def concat_bpk_list(self) -> str:
        return self.bpk_list[0].bpk + ("0" * 4)
