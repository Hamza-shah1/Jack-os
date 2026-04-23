import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel.kernel import Kernel
from gui.app import OSApp


def main():
    kernel = Kernel()
    kernel.boot()

    app = OSApp(kernel)
    app.run()


if __name__ == "__main__":
    main()
