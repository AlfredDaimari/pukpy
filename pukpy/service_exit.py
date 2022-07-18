class ServiceExit(Exception):
    """
    Error raise when SIGINT is received in main thread
    """
    pass
