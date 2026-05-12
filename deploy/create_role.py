import sys

"""Deprecated entrypoint: the AgentCore runtime role is now CDK-managed."""


def main() -> None:
    print("The AgentCore runtime role is now managed via CDK.")
    print("Run 'make create-role' instead of calling deploy/create_role.py directly.")
    sys.exit(1)


if __name__ == "__main__":
    main()
