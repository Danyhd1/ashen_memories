import random
import sys
import unittest


def flatten(suite):
    tests = []
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            tests.extend(flatten(test))
        else:
            tests.append(test)
    return tests


def main():
    seed = int(sys.argv[1])
    battle_only = "--battle" in sys.argv[2:]
    random.seed(seed)

    if battle_only:
        suite = unittest.defaultTestLoader.loadTestsFromName(
            "tests.test_battle_system"
        )
    else:
        suite = unittest.defaultTestLoader.discover("tests")
    tests = flatten(suite)
    random.shuffle(tests)

    result = unittest.TextTestRunner(verbosity=0).run(unittest.TestSuite(tests))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
