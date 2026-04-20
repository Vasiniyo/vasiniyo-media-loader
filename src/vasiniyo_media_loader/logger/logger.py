import logging
import traceback


class LogFormatter(logging.Formatter):
    def format(self, record):
        extras = [
            f"{k}={v!r}"
            for k, v in record.__dict__.items()
            if k
            not in (
                # fmt: off
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info", "lineno",
                "funcName", "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process", "taskName",
                # fmt: on
            )
        ]
        extras = " ".join(extras)
        trace = ""
        if record.exc_info:
            trace += "\n"
            trace += "".join(traceback.format_exception(*record.exc_info)).rstrip("\n")
        level = record.levelname
        message = record.getMessage()
        time = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        module = record.name
        return f"{time} {level} - {module} > msg={message!r} {extras}{trace}"
