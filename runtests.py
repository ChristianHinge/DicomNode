from unittest import TextTestRunner, TestSuite, TestLoader

if __name__ == "__main__":
  runner = TextTestRunner()
  loader = TestLoader()
  suite = loader.discover("src/dicomnode/tests")
  runner.run(suite)
