from flowglad.entrypoints import Input, entrypoint


@entrypoint
def transform(value: Input) -> dict[str, str]:
    return {"result": value.strip()}
