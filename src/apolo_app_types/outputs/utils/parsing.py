def parse_cli_args(args: list[str]) -> dict[str, str]:
    # Args could be in the form of '--key=value' or '--key value'
    result = {}
    i = 0
    # Before parsing, we need to split strings that might contain both key and value
    processed_args = []
    for arg in args:
        if not arg.startswith("-") and " " in arg:
            # This is not a standard way to pass args, but we handle it
            processed_args.extend(arg.split(" ", 1))
        # Handle cases like '--key value'
        elif arg.startswith("-") and " " in arg and "=" not in arg:
            processed_args.extend(arg.split(" ", 1))
        else:
            processed_args.append(arg)

    while i < len(processed_args):
        arg = processed_args[i]
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
        elif i + 1 < len(processed_args) and not processed_args[i + 1].startswith("-"):
            result[key] = processed_args[i + 1]
            i += 2
        else:
            result[key] = "true"
            i += 1
    return result
