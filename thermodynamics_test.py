# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
This module contains the test cases for the thermodynamics module.

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
11-02-2024		AW	create the test cases


"""
# Futures
from __future__ import print_function

# Specific Imports
from unittest.mock import MagicMock

# Built-in/Generic Imports
import unittest

# Own modules
from thermodynamics import (
    RoomLoad,
    Pressure,
    Bow,
    ComponentGeneral,
    ComponentRectangled,
    ComponentAirType,
    ComponentOrientation,
    CarbonDioxid,
    MetabolicRate,
    Converting,
)

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"thermodynamics_test.py"


class TestRoomLoad(unittest.TestCase):
    """
    Unit tests for the RoomLoad class.
    """

    def setUp(self):
        """
        Set up the test case by initializing the RoomLoad object.

        This method is called before each test method is executed.
        It creates a RoomLoad object with default values for persons, windows, walls, \
            and transmission types.
        """
        self.room_load = RoomLoad(
            persons=2, windows={}, walls={}, transmission_types={}
        )

    def test_post_init(self):
        """
        Test the __post_init__ method of the RoomLoad class.
        """
        self.room_load.radiation_dataframe = MagicMock()
        self.room_load.mean_transmission_coefficient = MagicMock()
        self.room_load.cooling_load_radiation = MagicMock()
        self.room_load.progression_cooling_load = MagicMock()
        self.room_load.heat_emission_dataframe = MagicMock()

        self.room_load.__post_init__()

        self.room_load.radiation_dataframe.assert_called_once()
        self.room_load.mean_transmission_coefficient.assert_called_once()
        self.room_load.cooling_load_radiation.assert_called_once()
        self.room_load.progression_cooling_load.assert_called_once()
        self.room_load.heat_emission_dataframe.assert_called_once()

    def test_load_total(self):
        """
        Test case for the load_total method of the RoomLoad class.

        This test verifies that the load_total method correctly calculates the total load
        based on the provided internal load, external load, and support system factor.

        The expected result is 150, which is calculated as follows:
        internal_load (100) + external_load (200) * support_system (0.5) = 150

        """
        result = self.room_load.load_total(
            internal_load=100, external_load=200, support_system=0.5
        )
        self.assertEqual(result, 150)


class TestCarbonDioxid(unittest.TestCase):
    """
    This class contains unit tests for the CarbonDioxid class.
    """

    def setUp(self):
        """
        Set up the test case by initializing the CarbonDioxid object.
        """
        self.carbon_dioxid = CarbonDioxid()

    def test_calculate_co2_persons(self):
        """
        Test case for the calculate_co2_persons method.

        This test verifies that the calculate_co2_persons method returns the correct result
        when given the number of adult persons, child persons, and activity level.

        The expected result for this test case is 35.2.

        """
        result = self.carbon_dioxid.calculate_co2_persons(
            persons_adult=2, persons_child=1, activity=MetabolicRate.BASE
        )
        self.assertEqual(result, 35.2)

    def test_conversion_flow(self):
        """
        Test the conversion flow method of the carbon_dioxid object.

        This method tests the conversion_flow method of the carbon_dioxid object by passing a flow \
            value of 3600 and
        the direction of conversion as M3_H_M3_S. It asserts that the result of the conversion is \
            equal to 1.
        """
        result = self.carbon_dioxid.conversion_flow(
            flow=3600, direction=Converting.M3_H_M3_S
        )
        self.assertEqual(result, 1)

    def test_calculate_room_volume(self):
        """
        Test case to verify the calculation of room volume.

        It calculates the room volume based on the given area and height,
        and checks if the calculated volume matches the expected volume.
        """
        self.carbon_dioxid.calculate_room_volume(area=10, height=2)
        self.assertEqual(self.carbon_dioxid.room_volume, 20)

    def test_calculate_co2_concentration(self):
        """
        Test case for the calculate_co2_concentration method.

        This method tests the calculate_co2_concentration method of the CarbonDioxide class.
        It verifies that the method returns the correct CO2 concentration based on the given inputs.

        Inputs:
        - flow_in: The flow rate of the gas in cubic meters per hour.
        - co2_generated: The amount of CO2 generated in grams per hour.

        Expected output:
        - The expected CO2 concentration in parts per million (ppm).

        """
        result = self.carbon_dioxid.calculate_co2_concentration(
            flow_in=3600, co2_generated=34
        )
        self.assertEqual(result, 318.45425147285096)


class TestPressure(unittest.TestCase):
    """
    Unit tests for the Pressure class.
    """

    def setUp(self):
        """
        Set up the test case by initializing the necessary objects.

        This method is called before each test method is executed.
        """
        self.connector = ComponentRectangled(
            general=ComponentGeneral(
                component_id="1",
                orientation=ComponentOrientation.VERTICAL,
                airtype=ComponentAirType.OA,
                port_a="port_a",
                port_b="port_b",
            ),
            width=600,
            heigth=200,
        )
        self.component = Bow(connector=self.connector, angle=90)
        self.pressure = Pressure(component=self.component, volume_flow=3600)

    def test_post_init(self):
        """
        Test method for the __post_init__ function of the Pressure class.
        """
        self.pressure._set_connector = MagicMock()
        self.pressure.set_mean_velocity = MagicMock()
        self.pressure.set_pressure_drop = MagicMock()

        self.pressure.__post_init__()

        self.pressure._set_connector.assert_called_once()
        self.pressure.set_mean_velocity.assert_called_once_with(
            volume_flow=self.pressure.volume_flow
        )
        self.pressure.set_pressure_drop.assert_called_once()

    def test_set_mean_velocity(self):
        """
        Test case for the 'set_mean_velocity' method.

        This test sets the area of the pressure connector to 1 and calls the 'set_mean_velocity' \
            method
        with a volume flow rate of 3600. It then checks if the mean velocity of the pressure is \
            equal to 1.
        """
        self.pressure.connector.area = 1
        self.pressure.set_mean_velocity(volume_flow=3600)
        self.assertEqual(self.pressure.mean_velocity, 1)

    def test_set_pressure_drop(self):
        """
        Test case for the set_pressure_drop method.

        This method sets the zeta value and mean velocity of the pressure component,
        and then calculates the pressure drop using the set_pressure_drop method.
        It asserts that the calculated pressure drop matches the expected value.
        """
        self.pressure.component.zeta_value = 1
        self.pressure.mean_velocity = 1
        self.pressure.set_pressure_drop()
        self.assertEqual(self.pressure.pressure_drop, 0.6465)


if __name__ == "__main__":
    unittest.main()
