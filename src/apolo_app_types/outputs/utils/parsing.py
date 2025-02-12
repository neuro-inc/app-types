import typing as t


def parse_cli_args(args: list[str]) -> dict[str, t.Any]:
    # Args could be in the form of '--key=value' or '--key value'
    result = {}
    for arg in args:
        if not arg.startswith(("-", "--")):
            print("Don't know how to handle argument:", arg)  # noqa: T201
            continue
        # you can pass any arguments to add_argument
        kv = arg.lstrip("-")
        if " " in kv:
            key, value = kv.split(" ", 1)
        else:
            key, value = kv.split("=", 1)
        result[key] = value
    return result
