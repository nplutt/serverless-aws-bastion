from click import secho, get_current_context
from serverless_aws_bastion.enum.log_level import LogLevel


def _get_log_level() -> LogLevel:
    """
    Fetches and returns the log level from the current context
    """
    log_level = get_current_context().params.get("log-level")

    try:
        return LogLevel[log_level.lower()]
    except KeyError:
        return LogLevel.info


def log_info(message: str) -> None:
    """
    Formats and prints out an info level message to the console
    """
    if _get_log_level() <= LogLevel.info:
        secho(message, fg="green")


def log_error(message: str) -> None:
    """
    Formats and prints out an error level message to the console
    """
    if _get_log_level() <= LogLevel.error:
        secho(f"Error: {message}", fg="red", err=True)
