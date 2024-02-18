# -*- coding: utf-8 -*-
"""
* DESCRIPTION:

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
10-02-2024		AW	creation of the file


"""
# Futures
from __future__ import print_function

# Built-in/Generic Imports
import unittest

# Own modules
from building_information import Building, Room

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"building_information_test.py"


class TestBuilding(unittest.TestCase):
    """
    This class contains unit tests for the Building class.
    """

    def setUp(self):
        self.room1 = Room(room_number="R1", persons=5, height=2.7)
        self.room1.set_area(length=5, width=5)
        self.room1.set_volume_flow(
            room_volume=self.room1.get_volume(), air_change_rate=5
        )

        self.room2 = Room(room_number="R2", persons=10, height=2.7)
        self.room2.set_area(length=10, width=10)
        self.room2.set_volume_flow(
            room_volume=self.room2.get_volume(), air_change_rate=7
        )

        self.building = Building(
            building_name="Test Building", rooms=[self.room1, self.room2]
        )

    def test_post_init(self):
        """
        Test case for the post initialization of the building object.
        It checks if the area, volume, persons, and air flow total of the building
        are correctly calculated based on the areas, volumes, persons, and volume flows
        of the rooms.
        """
        self.assertEqual(self.building.area, self.room1.area + self.room2.area)
        self.assertEqual(
            self.building.volume, self.room1.get_volume() + self.room2.get_volume()
        )
        self.assertEqual(self.building.persons, self.room1.persons + self.room2.persons)
        self.assertEqual(
            self.building.air_flow_total,
            self.room1.volume_flow + self.room2.volume_flow,
        )


class TestRoom(unittest.TestCase):
    """
    This class contains unit tests for the Room class.
    """

    def setUp(self):
        self.room = Room(room_number="R1", persons=5, height=2.7)
        self.room.set_area(length=5, width=5)
        self.room.set_volume_flow(room_volume=self.room.get_volume(), air_change_rate=5)

    def test_set_area(self):
        """
        Test case to verify the set_area method of the Room class.
        It checks if the area of the room is set correctly.
        """
        self.assertEqual(self.room.area, 25)

    def test_get_volume(self):
        """
        Test case for the get_volume method.

        This test case checks if the get_volume method returns the correct volume for a given room.
        It asserts that the returned volume is equal to 67.5.
        """
        self.assertEqual(self.room.get_volume(), 67.5)

    def test_set_volume_flow(self):
        """
        Test case for the set_volume_flow method.

        This method checks if the volume flow of the room is set correctly.
        It asserts that the volume flow of the room is equal to 337.5.
        """
        self.assertEqual(self.room.volume_flow, 337.5)


if __name__ == "__main__":
    unittest.main()
