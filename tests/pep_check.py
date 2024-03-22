import subprocess
import os


def pep_check():
    filepath = None
    with open("flake8_results.txt", "w") as f:
        subprocess.call(('py -m flake8 --exclude pyVenv/* --max-line-length 99'),
                        cwd="C:/Users/enzo/BH/bhpy", stdout=f)
    pass
    with open("flake8_results.txt", "r") as f:
        filepath = os.path.realpath(f.name)
    return filepath


def main():
    return pep_check()


if __name__ == '__main__':
    print(main())
