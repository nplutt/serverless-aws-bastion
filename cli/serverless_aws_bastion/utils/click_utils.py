from click import secho


def log_info(message: str) -> None:
    """
    Formats and prints out an info level message to the console
    """
    secho(message, fg="green")


def log_error(message: str) -> None:
    """
    Formats and prints out an error level message to the console
    """
    secho(f"Error: {message}", fg="red", err=True)
