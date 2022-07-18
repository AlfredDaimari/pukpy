import subprocess


class Jammer:
    """
    Jammer to jam signals
    """

    def __init__(self, i, m, f, s) -> None:
        self.i = i
        self.m = m
        self.f = f
        self.s = s
        self.proc = None

    def start(self) -> None:
        """
        start the jammer
        """
        if self.proc is not None:
            raise ChildProcessError("Jamming process is already running")
        self.proc = subprocess.Popen(["rpitx", "-i", self.i, "-m", self.m, "-f", self.f, "-s", self.s, "-l"])
        print("the jammer is now jamming")

    def stop(self) -> None:
        """
        stops the jammer
        """
        if self.proc is None:
            raise ChildProcessError("Jamming process is not running")
        subprocess.Popen.kill(self.proc)
        self.proc = None
        print("the jammer has stopped jamming")

