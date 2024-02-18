# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
unit tests for the evaluation_criteria module

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
10-02-2024		AW	create module


"""
# Futures
from __future__ import print_function

# Built-in/Generic Imports
import unittest

# Own modules
from evaluation_criteria import (
    ThermalComfort,
    AirQualityComfort,
    PersonType,
    ActivityType,
    RoomType,
    Room,
)

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"evaluation_criteria_test.py"


class TestThermalComfort(unittest.TestCase):
    """
    This class contains unit tests for the ThermalComfort class.
    """

    def setUp(self):
        self.comfort = ThermalComfort(
            air_temp=20, mean_radiant_temp=20, air_velocity=0.1, rel_humidity=50
        )

    def test_water_vapor_pressure(self):
        """
        Test case for the calculate_water_vapor_pressure method.

        This test verifies that the calculate_water_vapor_pressure method returns a float value.
        """
        result = self.comfort.calculate_water_vapor_pressure()
        self.assertIsInstance(result, float)

    def test_pmv_ppd(self):
        """
        Test case to check the types of pmv and ppd attributes in the Comfort class.
        """
        self.assertIsInstance(self.comfort.pmv, float)
        self.assertIsInstance(self.comfort.ppd, float)


class TestAirQualityComfort(unittest.TestCase):
    """
    This class contains unit tests for the AirQualityComfort class.
    """

    def setUp(self):
        self.room = Room(room_number="R1", persons=2, area=100)
        self.comfort = AirQualityComfort(
            persons={PersonType.ADULT: 1},
            activity={ActivityType.SITTING: 1},
            room_type=RoomType.OFFICE,
            room_data=self.room,
        )

    def test_room_contamination_load(self):
        """
        Test case for the room_contamination_load method.

        This method checks if the room_contamination_load method returns a float value.
        """
        result = self.comfort.room_contamination_load()
        self.assertIsInstance(result, float)

    def test_perceived_air_quality(self):
        """
        Test case for the perceived_air_quality method.

        This test verifies that the perceived_air_quality method returns a float value.

        Steps:
        1. Load the user contamination level.
        2. Load the room contamination level.
        3. Set the volume flow to 1,300.
        4. Call the perceived_air_quality method with the loaded contamination levels \
            and volume flow.
        5. Assert that the result is of type float.
        """
        user_contamination = self.comfort.user_contamination_load()
        room_contamination = self.comfort.room_contamination_load()
        volume_flow = 1_300
        result = self.comfort.perceived_air_quality(
            user_contamination, room_contamination, volume_flow
        )
        self.assertIsInstance(result, float)

    def test_percentage_dissatisfied(self):
        """
        Test case for the percentage_dissatisfied method.

        This method tests the percentage_dissatisfied method of the Comfort class.
        It verifies that the method returns a float value.

        Parameters:
        - self: The instance of the test class.

        Returns:
        - None
        """
        perceived_air_quality = 0.5
        result = self.comfort.percentage_dissatisfied(perceived_air_quality)
        self.assertIsInstance(result, float)


if __name__ == "__main__":
    unittest.main()
