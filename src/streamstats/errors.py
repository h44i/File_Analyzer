class StreamStatsError(Exception):
    pass


class Unsupported_Format_Error(StreamStatsError):
    pass


class Invalid_Event_Error(StreamStatsError):
    pass


class Invalid_Timestamp_Error(StreamStatsError):
    pass


class CLI_Config_Error(StreamStatsError):
    pass
