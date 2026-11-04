#!/usr/bin/env python3
"""Install or update mra-flow in an orchestrator repo. Run through install.sh."""
import sys

from installer.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
