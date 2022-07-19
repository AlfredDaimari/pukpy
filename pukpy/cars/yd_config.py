from rflib import MOD_ASK_OOK


class YdStickConfig:
    """
    class to hold yd_stick configs
    """

    def __init__(self, mod_type=MOD_ASK_OOK, freq_hz=433000000, channel=1, sync_mode=0, baud_rate=2500):
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
