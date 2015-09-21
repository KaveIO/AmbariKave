import unittest
import base
import pep8

LINES_SKIP = 17

class PEP8(pep8.StyleGuide):
    """This subclass of pep8.StyleGuide will skip the first lines of each file."""

    def input_file(self, filename, lines=None, expected=None, line_offset=0):
        if lines is None:
            assert line_offset == 0
            line_offset = LINES_SKIP
            lines = pep8.readlines(filename)[LINES_SKIP:]
        return super(PEP8, self).input_file(
            filename, lines=lines, expected=expected, line_offset=line_offset)

class TestCodeFormat(unittest.TestCase):

    def runTest(self):
        """Test that we conform to PEP8."""
        import os, string
        pep8style = PEP8(config_file=os.path.join(os.path.dirname(__file__),'pep8.conf'),quiet=True)
        allpyfiles=[]
        for root, dirs, files in os.walk(os.path.realpath(__file__+'/../../../')):
            allpyfiles=allpyfiles+[os.path.join(root,f) for f in files if f.endswith('.py')]
        result = pep8style.check_files(allpyfiles)
        print dir(result)
        for attr in dir(result):
            if '__' not in attr:
                print attr, '-----------'
                print getattr(result,attr)
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")



def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestCodeFormat())
    return suite


if __name__ == "__main__":
    base.run(suite())
