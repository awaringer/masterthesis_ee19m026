# -*- coding: utf-8 -*-
"""
* DESCRIPTION:

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
10-02-2024		AW	create test for import_data.py


"""
# Futures
from __future__ import print_function

# Built-in/Generic Imports
import unittest

# Libs
import pandas as pd

# Own modules
from import_data import ImportData, DocumentType, ImportType

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"import_data_test.py"


class TestImportData(unittest.TestCase):
    """
    A test case for the ImportData class.

    This test case verifies the behavior of the ImportData class by testing its \
    initialization and loading methods.
    """

    def setUp(self):
        self.import_data = ImportData(
            dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
            filename="LV_Madrid.xlsx",
            document_type=DocumentType.XLSX,
            import_flag=ImportType.WEATHER,
        )

    def test_post_init(self):
        """
        Test case for the post initialization of the ImportData object.
        """
        self.assertEqual(
            self.import_data.dirpath, "D:\\GitHub\\masterthesis\\masterthesis\\import"
        )
        self.assertEqual(self.import_data.filename, "LV_Madrid.xlsx")
        self.assertEqual(self.import_data.document_type, DocumentType.XLSX)
        self.assertEqual(self.import_data.import_flag, ImportType.WEATHER)
        self.assertIsNotNone(self.import_data.fullpath)
        self.assertIsInstance(self.import_data.data, pd.DataFrame)

    def test_load(self):
        """
        Test the load method of the ImportData class.

        This method tests whether the load method of the ImportData class returns a \
        pandas DataFrame object.

        Returns:
            None
        """
        df = self.import_data.load(
            fullpath=self.import_data.fullpath,
            document_type=self.import_data.document_type,
            import_flag=self.import_data.import_flag,
        )
        self.assertIsInstance(df, pd.DataFrame)


if __name__ == "__main__":
    unittest.main()
