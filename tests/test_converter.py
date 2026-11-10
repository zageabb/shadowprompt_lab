import unittest
from converter import convert, md_table

class ConversionTests(unittest.TestCase):
    def test_text(self):
        self.assertIn('hello', convert('example.txt', b'hello'))
    def test_csv(self):
        self.assertIn('| A | B |', convert('example.csv', b'A,B\n1,2'))
    def test_json(self):
        self.assertIn('"a": 1', convert('data.json', b'{"a":1}'))
    def test_unsupported(self):
        with self.assertRaises(ValueError): convert('evil.exe', b'abc')
    def test_empty(self):
        with self.assertRaises(ValueError): convert('x.txt', b'')
    def test_table(self):
        self.assertIn('| --- | --- |', md_table([['a','b'],['c','d']]))

if __name__ == '__main__': unittest.main()
