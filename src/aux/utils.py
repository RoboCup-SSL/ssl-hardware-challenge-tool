RED = "\033[0;31m"
BLUE = "\033[0;34m"
GREEN = "\033[0;92m"
PURPLE = "\033[0;95m"
RESET = "\033[0m"


def red_print(*kargs):
    print(RED, end="")
    end_c = '\n'
    if kargs[-1] == '\r':
        end_c = '\r'
    print(*kargs, end=end_c)
    print(RESET, end="")


def blue_print(*kargs):
    print(BLUE, end="")
    end_c = '\n'
    if kargs[-1] == '\r':
        end_c = '\r'
    print(*kargs, end=end_c)
    print(RESET, end="")


def green_print(*kargs):
    print(GREEN, end="")
    end_c = '\n'
    if kargs[-1] == '\r':
        end_c = '\r'
    print(*kargs, end=end_c)
    print(RESET, end="")


def purple_print(*kargs):
    print(PURPLE, end="")
    end_c = '\n'
    if kargs[-1] == '\r':
        end_c = '\r'
    print(*kargs, end=end_c)
    print(RESET, end="")
