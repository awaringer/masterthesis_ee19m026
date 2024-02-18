# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
unit test for air_components.py

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
from air_components import (
    ComponentGeneral,
    ComponentCircled,
    ComponentRectangled,
    Bow,
    ComponentOrientation,
    ComponentAirType,
)

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"air_components_test.py"


class TestComponentGeneral(unittest.TestCase):
    """
    This class contains unit tests for the ComponentGeneral class.
    """

    def setUp(self):
        self.component_general = ComponentGeneral(
            component_id="1",
            orientation=ComponentOrientation.VERTICAL,
            airtype=ComponentAirType.EA,
            port_a="PortA",
            port_b="PortB",
        )

    def test_str(self):
        """
        Test the __str__ method of the component_general object.
        """
        self.assertEqual(
            str(self.component_general),
            "-----------------------------------------------------------------------\nid: 1\nPort A: PortA, Port B: PortB",
        )


class TestComponentCircled(unittest.TestCase):
    """
    This class contains unit tests for the ComponentCircled class.
    """

    def setUp(self):
        self.component_circled = ComponentCircled(
            general=ComponentGeneral(
                component_id="1",
                orientation=ComponentOrientation.VERTICAL,
                airtype=ComponentAirType.EA,
                port_a="PortA",
                port_b="PortB",
            ),
            length=1000.0,
            diameter=500,
        )

    def test_post_init(self):
        """
        Test case for the post-initialization of the component.

        This test checks if the area of the component after initialization \
        is equal to the expected value.

        """
        self.assertEqual(self.component_circled.area, 0.19634954084936207)

    def test_str(self):
        """
        Test the __str__ method of the component_circled object.
        """
        self.assertEqual(
            str(self.component_circled),
            "-----------------------------------------------------------------------\nid: 1\nPort A: PortA, Port B: PortB\nshape form: ComponentForm.CIRCLED\nlength: 1000 [mm],\ndiameter: 500 [mm]\narea: 0.20 [m^2]",
        )


class TestComponentRectangled(unittest.TestCase):
    """
    This class contains unit tests for the ComponentRectangled class.
    """

    def setUp(self):
        self.component_rectangled = ComponentRectangled(
            general=ComponentGeneral(
                component_id="1",
                orientation=ComponentOrientation.VERTICAL,
                airtype=ComponentAirType.EA,
                port_a="PortA",
                port_b="PortB",
            ),
            length=1000.0,
            width=500,
            heigth=500,
        )

    def test_post_init(self):
        """
        Test case for the post initialization of the component.
        It checks if the area of the component is correctly set to 0.25.
        """
        self.assertEqual(self.component_rectangled.area, 0.25)

    def test_str(self):
        """
        Test the __str__ method of the component_rectangled object.
        """
        self.assertEqual(
            str(self.component_rectangled),
            "-----------------------------------------------------------------------\nid: 1\nPort A: PortA, Port B: PortB\nshape form: ComponentForm.RECTANGLED\nlength: 1000 [mm]\nwidth a: 500 [mm], heigth a: 500 [mm]\narea: 0.25 [m^2]",
        )


class TestBow(unittest.TestCase):
    """
    This class contains unit tests for the Bow component.
    """

    def setUp(self):
        self.bow = Bow(
            connector=ComponentCircled(
                general=ComponentGeneral(
                    component_id="1",
                    orientation=ComponentOrientation.VERTICAL,
                    airtype=ComponentAirType.EA,
                    port_a="PortA",
                    port_b="PortB",
                ),
                length=1000.0,
                diameter=500,
            ),
            angle=90.0,
        )


if __name__ == "__main__":
    unittest.main()
