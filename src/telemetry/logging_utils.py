"""Module for setting up and managing a global logger instance."""

import logging


class Logger:
    """
    Class containing the global logger instance.
    """

    _logger = None

    @classmethod
    def setup_logging(cls) -> None:
        """
        Configure logging for the project.
        """
        if cls._logger is None:
            logging.basicConfig(
                format="[%(asctime)s][%(levelname)s][%(funcName)s] %(message)s",
                level=logging.INFO,  # Set the desired log level here
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            cls._logger = logging.getLogger("Logger")

            # add compatibility with opentelemetry
            otel_loggers = [
                "opentelemetry.sdk",
                "opentelemetry.trace",
                "opentelemetry.exporter.otlp.proto.http.trace_exporter",
            ]

            for name in otel_loggers:
                logging.getLogger(name).setLevel(logging.DEBUG)

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Returns the global logger instance.
        """
        if cls._logger is None:
            cls.setup_logging()  # Ensure logging is set up before returning the logger
        return cls._logger
