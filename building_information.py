# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
In this module, the classes for the building and the rooms are defined. \
The building class holds the rooms and sums up the properties of the rooms in the building. \
The room class holds the properties of a room and calculates the volume flow of the room.

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
10-02-2024		AW	creation of module


"""
# Futures
from __future__ import print_function

# Specific Imports
from dataclasses import dataclass, field
from typing import Union

# Built-in/Generic Imports
import icecream as ic

# Own modules
from air_components import ComponentCircled, ComponentRectangled, ComponentType

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"building_information.py"


@dataclass
class Building:
    """building class to hold the rooms and sum up the properties of the rooms in the building"""

    building_name: str
    rooms: list
    area: float = field(init=False)
    volume: float = field(init=False)
    persons: int = field(init=False)
    air_flow_total: float = field(init=False)

    def __post_init__(self) -> None:
        self.set_sum_properties()

    def set_sum_properties(self) -> None:
        """sum up the properties of the rooms in the building"""
        # initialize the sum properties
        self.area = 0
        self.volume = 0
        self.persons = 0
        self.air_flow_total = 0

        # sum up the properties of the rooms
        for room in self.rooms:
            self.area += room.area
            self.volume += room.get_volume()
            self.persons += room.persons
            self.air_flow_total += room.volume_flow


@dataclass
class Room:
    """room class to hold the properties of a room and calculate the volume flow of the room"""

    room_number: str
    connector: Union[ComponentCircled, ComponentRectangled]
    persons: int
    componenttype: ComponentType = ComponentType.ROOM
    area: float = field(default=1)
    height: float = field(default=2.5)
    volume_flow: float = field(init=False, default=0)
    zeta_value: float = 0

    def set_area(self, length: float, width: float) -> None:
        """set the area of the room

        Args:
            length (float): room length [m]
            width (float): room width [m]
        """
        self.area = length * width

    def get_volume(self) -> float:
        """set the volume of the room

        Returns:
            float: room volume [m³]
        """
        return self.area * self.height

    def set_volume_flow(self, room_volume: float, air_change_rate: float) -> None:
        """set the volume flow of the room

        Args:
            room_volume (float): room volume [m³]
            air_change_rate (float): air change rate [1/h]
        """
        self.volume_flow = room_volume * air_change_rate


# Main - Test Environment
if __name__ == "__main__":
    pass
    # rooms_list = []
    # ROOM_NUMBER = "R1"
    # PERSONS = 5
    # LENGTH = 5
    # WIDTH = 5
    # HEIGHT = 2.7
    # test_room = Room(room_number=ROOM_NUMBER, persons=PERSONS, height=HEIGHT)
    # test_room.set_area(length=LENGTH, width=WIDTH)
    # room_volume_R1 = test_room.get_volume()
    # test_room.set_volume_flow(room_volume=room_volume_R1, air_change_rate=5)
    # rooms_list.append(test_room)
    # # ic.ic(test_room)
    # ROOM_NUMBER2 = "R2"
    # PERSONS2 = 10
    # LENGTH2 = 10
    # WIDTH2 = 10
    # HEIGHT2 = 2.7
    # test_room2 = Room(room_number=ROOM_NUMBER2, persons=PERSONS2, height=HEIGHT2)
    # test_room2.set_area(length=LENGTH2, width=WIDTH2)
    # room_volume_R2 = test_room.get_volume()
    # test_room2.set_volume_flow(room_volume=room_volume_R2, air_change_rate=7)
    # rooms_list.append(test_room2)
    # # ic.ic(test_room2)
    # # ic.ic(rooms_list)
    # building_test = Building(building_name="Test Building", rooms=rooms_list)
    # ic.ic(building_test)
