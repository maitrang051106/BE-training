import unittest


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover('tests', pattern='*_test.py'))
    runner = unittest.TextTestRunner(verbosity=2)
    raise SystemExit(not runner.run(suite).wasSuccessful())
