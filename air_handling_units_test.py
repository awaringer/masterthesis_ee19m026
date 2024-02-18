# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
unit test for air_handling_units.py

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
10-02-2024		AW	creation of module


"""
# Futures
from __future__ import print_function

# Built-in/Generic Imports
import unittest

# Own modules
from air_handling_units import Fan, Register, RegisterType, UnitType

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"air_handling_units_test.py"


class TestFan(unittest.TestCase):
    """
    This class contains unit tests for the Fan class.
    """

    def setUp(self):
        self.fan = Fan(volume_flow_nominal=1000.0, electrical_power_nominal=500.0)

    def test_post_init(self):
        """
        Test case for the post initialization of the air handling unit.
        """
        self.assertEqual(self.fan.unit_type, UnitType.FAN)
        self.assertIsNotNone(self.fan.sfp_class)
        self.assertIsNotNone(self.fan.efficiency)

    def test_get_sfp_class_efficiency(self):
        """
        Test case for the get_sfp_class_efficiency method.

        This method tests the functionality of the get_sfp_class_efficiency method
        by passing a volume flow and electrical power and checking the return type.

        Parameters:
        - volume_flow (float): The volume flow in cubic meters per hour.
        - electrical_power (float): The electrical power in watts.

        Returns:
        - None

        Raises:
        - AssertionError: If the return type is not an integer.
        """
        sfp_class = self.fan.get_sfp_class_efficiency(
            volume_flow=1000.0, electrical_power=500.0
        )
        self.assertIsInstance(sfp_class, int)

    def test_calculate_current_power(self):
        """
        Test case for the calculate_current_power method of the Fan class.
        It verifies that the method returns a float value.
        """
        current_power = self.fan.calculate_current_power(volume_flow=1000.0)
        self.assertIsInstance(current_power, float)


class TestRegister(unittest.TestCase):
    """
    A test case for the Register class.
    """

    def setUp(self):
        self.register = Register(register_type=RegisterType.HEATING, max_power=1000.0)

    def test_init(self):
        """
        Test case for the initialization of the air handling unit.
        """
        self.assertEqual(self.register.unit_type, UnitType.REGISTER)


if __name__ == "__main__":
    unittest.main()
