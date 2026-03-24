from smart_agent_arch import ExtensionRegistry, LibraryConfig


def main() -> None:
    config = LibraryConfig(project_name="nexlab-lib", debug=True, environment="dev")
    config.validate()

    registry = ExtensionRegistry()
    registry.register("normalize", lambda text: text.strip().lower())

    result = registry.call("normalize", "  HeLLo NexLab  ")
    print(result)


if __name__ == "__main__":
    main()
