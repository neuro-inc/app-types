def parse_cli_args(args: list[str]) -> dict[str, str]:
    # Args could be in the form of '--key=value' or '--key value'
    result = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if not arg.startswith(("-", "--")):
            print("Don't know how to handle argument:", arg)  # noqa: T201
            i += 1
            continue
        # you can pass any arguments to add_argument
        key = arg.lstrip("-")
        if "=" in key:
            key, value = key.split("=", 1)
            result[key] = value
            i += 1
        elif i + 1 < len(args) and not args[i + 1].startswith("-"):
            result[key] = args[i + 1]
            i += 2
        else:
            result[key] = "true"
            i += 1
    return result
