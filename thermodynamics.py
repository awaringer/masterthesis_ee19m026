# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
This module contains the classes and functions for the thermodynamics calculations.

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------


"""
# Futures
from __future__ import print_function

# Specific Imports
from dataclasses import dataclass, field
from enum import Enum, auto
from msilib.schema import Component
from typing import Dict, List, Union

# Libs
import math
import pendulum
import pandas as pd
import icecream as ic

# Own Libs
from air_components import (
    Duct,
    Bow,
    Reduction,
    TPiece,
    ComponentType,
    ComponentGeneral,
    ComponentRectangled,
    ComponentOrientation,
    ComponentAirType,
    ComponentForm,
    Flap,
)
from building_information import Room


__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"thermodynamics.py"


class TemperatureType(Enum):
    """Represents the temperature types for heat recovery.

    Attributes:
        CELSIUS: Represents temperature in Celsius.
        KELVIN: Represents temperature in Kelvin.
        FAHRENHEIT: Represents temperature in Fahrenheit.
    """

    CELSIUS = auto()
    KELVIN = auto()
    FAHRENHEIT = auto()


class HumidityType(Enum):
    """Enumeration representing humidity types.

    This enumeration defines the different types of humidity that can be used in thermodynamics \
        calculations.

    Attributes:
        RELATIV: Represents relative humidity.
        ABSOLUT: Represents absolute humidity.
    """

    RELATIV = auto()
    ABSOLUT = auto()


class MetabolicRate(Enum):
    """Metabolic Rate enumeration.

    This enumeration represents different levels of metabolic rates.

    Attributes:
        BASE: The base metabolic rate.
        RELAXED_SITTING: The metabolic rate during relaxed sitting.
        LIGHT_SEDENTARY: The metabolic rate during light sedentary activities.
        LIGHT_STANDING: The metabolic rate during light standing activities.
        STANDING_MODERATE_ACTIVITY: The metabolic rate during standing with moderate activity.
    """

    BASE = auto()
    RELAXED_SITTING = auto()
    LIGHT_SEDENTARY = auto()
    LIGHT_STANDING = auto()
    STANDING_MODERATE_ACTIVITY = auto()


class Converting(Enum):
    """Conversion Direction

    This enumeration represents the different conversion directions for thermodynamic calculations.
    Each member of this enumeration represents a specific conversion direction.
    """

    M3_H_M3_S = auto()
    M3_S_M3_H = auto()


@dataclass
class RoomLoad:
    """
    Class representing the room load calculations.

    Attributes:
        persons (int): Number of persons in the room.
        windows (Dict[str, float]): Dictionary containing the properties of the windows.
        walls (Dict[str, float]): Dictionary containing the properties of the walls.
        transmission_types (Dict[str, str]): Dictionary containing the types of transmission.
        radiation_windows (pd.DataFrame): DataFrame containing the radiation values for windows.
        mean_transmission (dict): Dictionary containing the mean transmission coefficients.
        cooling_load_factor_radiation (pd.DataFrame): DataFrame containing the cooling load factors\
             for radiation.
        cooling_load_factor_machine (pd.DataFrame): DataFrame containing the cooling load factors \
            for machines.
        heat_emissions (pd.DataFrame): DataFrame containing the heat emissions from people.

    Methods:
        __post_init__(): Performs post-initialization tasks for the class.
        load_total(internal_load: float, external_load: float, support_system: float) -> float: \
            Calculates the total room load.
        load_internal(load_persons: float, load_light: float, load_machines: float, \
            load_diff_temperature: float) -> float: Calculation of the total internal load.
        load_persons(heat_emission: float, load_factor: float) -> float: Calculate the load \
            due to persons.
        heat_emission_dataframe() -> pd.DataFrame: Compilation of the heat emission from people.
        load_light(power: float, simultaneity: float, room_load_factor: float, load_factor: float) \
            -> float: Calculates the load due to lighting.
        load_machines(simultaneity: float, load_factor: float, sum_machine_power: float) -> float: \
            Calculation of the load due to machines and equipment.
        sum_machines_power(power_efficiency: Dict[float, float], load_factors: List[float]) \
            -> float: Sum up the power of machines and equipments.
        radiation_dataframe() -> pd.DataFrame: Compilation with standard values for the monthly \
            maxima of the total radiation through two glazed surfaces.
        mean_transmission_coefficient() -> dict: Calculates the mean transmission coefficient of \
            solar radiation.
    """

    persons: int
    windows: Dict[str, float]
    walls: Dict[str, float]
    transmission_types: Dict[str, str]
    radiation_windows: pd.DataFrame = field(init=False)
    mean_transmission: dict = field(init=False)
    cooling_load_factor_radiation: pd.DataFrame = field(init=False)
    cooling_load_factor_machine: pd.DataFrame = field(init=False)
    heat_emissions: pd.DataFrame = field(init=False)

    def __post_init__(self):
        """
        Performs post-initialization tasks for the class.

        This method initializes the `radiation_windows`, `mean_transmission`,
        `cooling_load_factor_radiation`, `cooling_load_factor_machine`, and
        `heat_emissions` attributes of the class.

        Returns:
            None
        """
        self.radiation_windows = self.radiation_dataframe()
        self.mean_transmission = self.mean_transmission_coefficient()
        self.cooling_load_factor_radiation = self.cooling_load_radiation()
        self.cooling_load_factor_machine = self.progression_cooling_load()
        self.heat_emissions = self.heat_emission_dataframe()

    def load_total(
        self, internal_load: float, external_load: float, support_system: float
    ) -> float:
        """
        Calculates the total room load.

        Args:
            internal_load (float): The total of all internal loads. [W]
            external_load (float): The total of all external loads. [W]
            support_system (float): The share of the supporting system as a percentage (0 to 1).

        Returns:
            float: The total power dissipation through the ventilation system. [W]
        """
        return (
            internal_load
            + external_load
            - (internal_load + external_load) * support_system
        )

    def load_internal(
        self,
        load_persons: float,
        load_light: float,
        load_machines: float,
        load_diff_temperature: float,
    ) -> float:
        """
        Calculation of the total internal load Q_I.

        Args:
            load_persons (float): Sum of load due to persons [W].
            load_light (float): Sum of load due to lighting [W].
            load_machines (float): Sum of load due to machines and equipment [W].
            load_diff_temperature (float): Sum of load due to temperature difference [W].

        Returns:
            float: Total internal load [W].
        """
        return sum(load_persons, load_light, load_machines, load_diff_temperature)

    def load_persons(self, heat_emission: float, load_factor: float) -> float:
        """
        Calculate the load due to persons.

        Args:
            heat_emission (float): Heat emission from the human body [W].
            load_factor (float): Load factor for internal loads [W].

        Returns:
            float: Total load due to persons [W].
        """
        # Q_P = n * q_P * S_i
        return self.persons * heat_emission * load_factor

    def heat_emission_dataframe(self) -> pd.DataFrame:
        """Compilation of the heat emission from people
        according to VDI 2078 Table A1

        Returns:
            pd.DataFrame: personal heat depending on temperature
        """
        idx = [18, 20, 22, 23, 24, 25, 26]
        personal_heat = []

        no_physical = pd.Series(
            data=[125, 120, 120, 120, 115, 115, 115],
            index=idx,
            name="no physical activity",
        )
        personal_heat.append(no_physical)

        moderate_physical = pd.Series(
            data=[190, 190, 190, 190, 190, 190, 190],
            index=idx,
            name="moderately heavy physical activity",
        )
        personal_heat.append(moderate_physical)

        heavy_physical = pd.Series(
            data=[270, 270, 270, 270, 270, 270, 270],
            index=idx,
            name="heavy physical activity",
        )
        personal_heat.append(heavy_physical)
        return pd.DataFrame(data=personal_heat)

    def load_light(
        self,
        power: float,
        simultaneity: float,
        room_load_factor: float,
        load_factor: float,
    ) -> float:
        """Calculates the load due to lighting.

        This function calculates the total lighting load based on the given parameters.

        Args:
            power (float): Total installed power of the lights. [W]
            simultaneity (float): Simultaneity factor of the lighting at the time.
            room_load_factor (float): Room load factor due to lighting.
            load_factor (float): Cooling load factor for internal loads.

        Returns:
            float: Total lighting load. [W]
        """
        # Q_B = P * l * my_B * S_i
        return power * simultaneity * room_load_factor * load_factor

    def load_machines(
        self, simultaneity: float, load_factor: float, sum_machine_power: float
    ) -> float:
        """
        Calculation of the load due to machines and equipment Q_M.

        Args:
            simultaneity (float): Simultaneity factor [0..1] %
            load_factor (float): Cooling load factor for internal loads [W]
            sum_machine_power (float): Total power of machines [W]

        Returns:
            float: Total cooling load due to machines and equipment [W]
        """
        # Q_M = l * S_i * sum_machine_power
        return simultaneity * load_factor * sum_machine_power

    def sum_machines_power(
        self, power_efficiency: Dict[float, float], load_factors: List[float]
    ) -> float:
        """Sum up the power of machines and equipments based on their efficiency and load factors.

        Args:
            power_efficiency (Dict[float, float]): A dictionary representing the dependency of \
                power and efficiency of each machine.
            load_factors (List[float]): A list of load factors for each machine at the time in \
                question.

        Returns:
            float: The total power of all machines and equipments.
        """
        sum_power = 0

        for power, efficiency, load_factor in zip(
            power_efficiency.items(), load_factors
        ):
            power_temp = (power / efficiency) * load_factor

            sum_power = sum_power + power_temp

        return sum_power

    def radiation_dataframe(self) -> pd.DataFrame:
        """Compilation with standard values for the monthly maxima of
        the total radiation through two glazed surfaces according to
        VDI 2078 Table A11

        Returns:
            pd.DataFrame: table with radiation
        """
        idx = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "Dezember",
        ]
        direction = []
        default = pd.Series(
            data=[650, 706, 762, 780, 778, 747, 743, 739, 716, 705, 622, 586],
            index=idx,
            name="default",
        )
        direction.append(default)
        northeast = pd.Series(
            data=[45, 68, 179, 307, 384, 385, 357, 278, 154, 68, 45, 38],
            index=idx,
            name="Northeast",
        )
        direction.append(northeast)
        east = pd.Series(
            data=[279, 373, 477, 551, 563, 533, 528, 508, 433, 376, 259, 202],
            index=idx,
            name="East",
        )
        direction.append(east)
        southeast = pd.Series(
            data=[526, 581, 607, 570, 507, 458, 481, 534, 565, 581, 498, 464],
            index=idx,
            name="Southeast",
        )
        direction.append(southeast)
        south = pd.Series(
            data=[612, 627, 599, 509, 400, 347, 385, 483, 563, 626, 586, 561],
            index=idx,
            name="South",
        )
        direction.append(south)
        southwest = pd.Series(
            data=[526, 581, 607, 570, 507, 458, 481, 534, 565, 581, 498, 464],
            index=idx,
            name="Southwest",
        )
        direction.append(southwest)
        west = pd.Series(
            data=[279, 373, 477, 551, 563, 533, 528, 508, 433, 376, 259, 202],
            index=idx,
            name="West",
        )
        direction.append(west)
        northwest = pd.Series(
            data=[45, 68, 179, 307, 384, 385, 357, 278, 154, 68, 45, 38],
            index=idx,
            name="Northwest",
        )
        direction.append(northwest)
        north = pd.Series(
            data=[46, 59, 74, 86, 93, 97, 94, 87, 76, 58, 45, 38],
            index=idx,
            name="North",
        )
        direction.append(north)
        horizontal = pd.Series(
            data=[168, 286, 455, 585, 659, 657, 631, 554, 431, 286, 161, 113],
            index=idx,
            name="Horizontal",
        )
        direction.append(horizontal)
        return pd.DataFrame(data=direction)

    def mean_transmission_coefficient(self) -> dict:
        """
        Calculates the mean transmission coefficient b of solar radiation
        according to the VDI 2078 table A13.

        Returns:
            dict: Compilation of mean transmission coefficients.
        """
        mean_transmission_glass = {
            "sheet_single": 1.1,
            "sheet_double": 1.0,
            "sheet_triple": 0.9,
            "absorption_single": 0.75,
            "absorption_double": 0.65,
            "absorption_triple": 0.50,
            "reflective_single": 0.65,
            "reflective_metal_oxide": 0.55,
            "reflective_noble_metal": 0.45,
            "smooth_without_glass": 0.65,
            "smooth_with_glass": 0.45,
            "structured_without_glass": 0.45,
            "structured_with_glass": 0.35,
        }
        mean_transmission_sun_protection = {
            "external_blind_45_degree": 0.15,
            "external_cloth_ventilated": 0.3,
            "external_cloth_close": 0.4,
            "between_blind_45_degree": 0.5,
            "internal_blind_45_degree": 0.7,
            "internal_curtains": 0.5,
            "interla_plastic_films": 0.7,
            "internal_metalic": 0.35,
        }
        return {**mean_transmission_glass, **mean_transmission_sun_protection}

    def progression_cooling_load(self) -> pd.DataFrame:
        """
        Calculates the cooling load factors for machines according to VDI 2078 Table A5.
        This calculation is specific for Room type M "medium" and the commencement of gain is at
        8 am, and the end of gain is at 4 pm.

        Returns:
            pd.DataFrame: Cooling load factor for room type medium.
        """
        cooling_load_factor = []

        idx = list(range(1, 25, 1))
        medium_20_0_0 = pd.Series(
            data=[
                0.16,
                0.15,
                0.14,
                0.13,
                0.12,
                0.11,
                0.10,
                0.09,
                0.50,
                0.55,
                0.59,
                0.62,
                0.65,
                0.68,
                0.71,
                0.73,
                0.34,
                0.30,
                0.27,
                0.25,
                0.23,
                0.21,
                0.19,
                0.18,
            ],
            index=idx,
            name="Room Type Medium, Furniture: 20%, Lights: 0%, Internal Gain: 0%",
        )
        cooling_load_factor.append(medium_20_0_0)

        medium_20_30_30 = pd.Series(
            data=[
                0.11,
                0.10,
                0.10,
                0.09,
                0.08,
                0.08,
                0.07,
                0.07,
                0.65,
                0.68,
                0.71,
                0.74,
                0.76,
                0.78,
                0.79,
                0.81,
                0.24,
                0.21,
                0.19,
                0.17,
                0.16,
                0.15,
                0.13,
                0.12,
            ],
            index=idx,
            name="Room Type Medium, Furniture: 20%, Lights: 30%, Internal Gain: 30%",
        )
        cooling_load_factor.append(medium_20_30_30)

        medium_20_50_40 = pd.Series(
            data=[
                0.08,
                0.07,
                0.07,
                0.06,
                0.06,
                0.05,
                0.05,
                0.05,
                0.75,
                0.77,
                0.79,
                0.81,
                0.83,
                0.84,
                0.85,
                0.86,
                0.17,
                0.15,
                0.14,
                0.12,
                0.11,
                0.10,
                0.10,
                0.09,
            ],
            index=idx,
            name="Room Type Medium, Furniture: 20%, Lights: 50%, Internal Gain: 40%",
        )
        cooling_load_factor.append(medium_20_50_40)

        cooling_load_factor = pd.DataFrame(data=cooling_load_factor)
        return cooling_load_factor

    def load_diff_temperature(
        self, heat_transmission: float, delta_temp: float
    ) -> float:
        """
        Calculate the load due to different temperatures in adjacent rooms.

        Args:
            heat_transmission (float): The heat transmission coefficient. [W/m²K]
            delta_temp (float): The temperature difference. [K]

        Returns:
            float: The sum of the load due to different temperatures in adjacent rooms [W].
        """
        load_sum = 0

        for _, walls_value in self.walls.items():
            # Q_R = k * A * dT
            load_temp = heat_transmission * walls_value * delta_temp

            load_sum = load_sum + load_temp

        return load_sum

    def load_external(
        self,
        load_external_walls: float,
        load_transmission_windows: float,
        load_radiation_windows: float,
    ) -> float:
        """Calculate the total external load Q_A.

        This method calculates the total external load Q_A by summing the load through
        external walls, the load due to transmission through windows, and the load due
        to radiation of windows.

        Args:
            load_external_walls (float): The sum of load through external walls [W].
            load_transmission_windows (float): The sum of load due to transmission [W].
            load_radiation_windows (float): The sum of load due to radiation of windows [W].

        Returns:
            float: The total load of external influences [W].
        """
        # Q_A = Q_W + Q_T + Q_S
        return sum(
            load_external_walls, load_transmission_windows, load_radiation_windows
        )

    def load_external_walls(
        self, heat_transmission: float, delta_temp_eqivalent: float
    ) -> float:
        """Calculate the load through external walls and roofs.

        This method calculates the load through external walls and roofs based on the heat \
            transmission coefficient and the equivalent temperature difference.

        Args:
            heat_transmission (float): The heat transmission coefficient.
            delta_temp_eqivalent (float): The equivalent temperature difference.

        Returns:
            float: The sum of the load through external walls [W].
        """
        load_external_walls_sum = 0

        # loop if more elements per room
        for _, wall_value in self.walls.items():
            # Q_W = k * A * dT_eq
            external_wall_temp = heat_transmission * wall_value * delta_temp_eqivalent

            load_external_walls_sum = load_external_walls_sum + external_wall_temp

        return load_external_walls_sum

    def load_transmission_windows(
        self,
        heat_transmission: float,
        external_temperature: float,
        room_temperature: float,
    ) -> float:
        """Calculate the load due to transmission through windows.

        This method calculates the load due to transmission through windows
        based on the heat transmission coefficient of the window, the instantaneous
        external air temperature, and the room air temperature.

        Args:
            heat_transmission (float): The heat transmission coefficient of the window.
            external_temperature (float): The instantaneous external air temperature.
            room_temperature (float): The room air temperature.

        Returns:
            float: The sum of load due to transmission [W].
        """
        transmission_load_sum = 0

        # Loop through each window in the room
        for _, window_value in self.windows.items():
            # Calculate the load due to transmission for each window
            transmission_load_temp = (
                heat_transmission
                * window_value
                * (external_temperature - room_temperature)
            )

            # Add the load due to transmission for each window to the total sum
            transmission_load_sum += transmission_load_temp

        return transmission_load_sum

    def cooling_load_radiation(self) -> pd.DataFrame:
        """
        Calculates the cooling load factor according to the VDI 2078 table A16.

        Returns:
            pd.DataFrame: Cooling load factor for July/September (normal external/internal).
        """
        cooling_load_factor = []
        idx = list(range(1, 25, 1))
        july_normal_external = pd.Series(
            data=[
                0.08,
                0.07,
                0.07,
                0.07,
                0.23,
                0.47,
                0.65,
                0.76,
                0.84,
                0.88,
                0.90,
                0.91,
                0.91,
                0.90,
                0.87,
                0.81,
                0.71,
                0.55,
                0.31,
                0.12,
                0.09,
                0.09,
                0.09,
                0.08,
            ],
            index=idx,
            name="july normal external",
        )
        cooling_load_factor.append(july_normal_external)
        july_normal_internal = pd.Series(
            data=[
                0.04,
                0.04,
                0.04,
                0.03,
                0.22,
                0.49,
                0.68,
                0.81,
                0.88,
                0.92,
                0.94,
                0.95,
                0.95,
                0.93,
                0.90,
                0.83,
                0.72,
                0.53,
                0.28,
                0.06,
                0.05,
                0.05,
                0.04,
                0.04,
            ],
            index=idx,
            name="july normal internal",
        )
        cooling_load_factor.append(july_normal_internal)

        september_normal_external = pd.Series(
            data=[
                0.06,
                0.06,
                0.05,
                0.05,
                0.05,
                0.09,
                0.36,
                0.60,
                0.74,
                0.83,
                0.87,
                0.89,
                0.89,
                0.86,
                0.79,
                0.67,
                0.45,
                0.16,
                0.09,
                0.08,
                0.07,
                0.07,
                0.07,
                0.06,
            ],
            index=idx,
            name="september normal external",
        )
        cooling_load_factor.append(september_normal_external)
        september_normal_internal = pd.Series(
            data=[
                0.03,
                0.03,
                0.03,
                0.03,
                0.03,
                0.08,
                0.39,
                0.64,
                0.80,
                0.86,
                0.93,
                0.94,
                0.94,
                0.90,
                0.82,
                0.68,
                0.43,
                0.11,
                0.05,
                0.04,
                0.04,
                0.04,
                0.04,
                0.03,
            ],
            index=idx,
            name="september normal internal",
        )
        cooling_load_factor.append(september_normal_internal)
        cooling_load_factor = pd.DataFrame(data=cooling_load_factor)
        return cooling_load_factor

    def get_heat_emission(self, temperature: int, activity: str) -> float:
        """
        Return the selected personal heat emission depending on temperature and activity.

        Args:
            temperature (int): Room air temperature [°C].
            activity (str): Specific activity string.

        Returns:
            float: Personal heat emission [W].
        """
        return self.heat_emissions.loc[activity][int(temperature)]

    def get_cooling_load_factor_machine(
        self, date_time: pendulum.datetime, room_type_equipment: str
    ) -> float:
        """
        Return the selected cooling factor depending on the datetime.

        Args:
            date_time (pendulum.datetime): Target date for evaluation of cooling load factor.
            room_type_equipment (str): Definition of given room types including the equipment load.

        Returns:
            float: Cooling factor coefficient.
        """
        return self.cooling_load_factor_machine.loc[room_type_equipment][date_time.hour]

    def get_cooling_load_factor_radiation(
        self, date_time: pendulum.datetime, factor_type: str
    ) -> float:
        """Return the selected cooling factor depending on the datetime.

        Args:
            date_time (pendulum.datetime): Target date for evaluation of cooling load factor.
            factor_type (str): Definition of the given factor type.

        Returns:
            float: Cooling factor coefficient.
        """
        return self.cooling_load_factor_radiation.loc[factor_type][date_time.hour]

    def get_radiation_window(
        self, date_time: pendulum.datetime, orientation: str
    ) -> float:
        """
        Return the selected radiation for the window depending on the month.

        Args:
            date_time (pendulum.datetime): Target month for evaluation of the radiation value.
            orientation (str): Orientation of the window.

        Returns:
            float: Radiation coefficient.
        """
        return self.radiation_windows.loc[orientation][date_time.month]

    def load_radiation_windows(
        self,
        cooling_load_factor: float,
        radiation_window: float,
    ) -> float:
        """Calculate the cooling load due to window radiation.

        This method calculates the cooling load due to window radiation based on the given cooling
        load factor and radiation window values.

        Args:
            cooling_load_factor (float): The cooling load factor referring to hour and factor type.
            radiation_window (float): The radiation window value referring to month and orientation.

        Returns:
            float: The sum of the load due to radiation of windows. [W]

        """
        cooling_load_sum = 0

        # Loop through each window in the room
        for window_key, window_value in self.windows.items():
            radiant_transmission_coefficient = self.mean_transmission[
                self.transmission_types[window_key]
            ]

            # Calculate the cooling load due to window radiation
            cooling_load_temp = (
                (window_value * radiation_window)
                * radiant_transmission_coefficient
                * cooling_load_factor
            )  # Qs

            cooling_load_sum = cooling_load_sum + cooling_load_temp  # Qs_total

        return cooling_load_sum


@dataclass
class CarbonDioxid:
    """
    Represents the carbon dioxide levels in a room and provides methods to calculate CO2 \
        concentrations.

    Attributes:
        outdoor_co2 (float): The default outdoor CO2 concentration in parts per million (ppm).
        room_co2 (float): The default room CO2 concentration in parts per million (ppm).
        room_volume (float): The default volume of the room in cubic meters (m³).
        persons_adult (int): The default number of adults in the room.
        persons_child (int): The default number of children in the room.
    
    Methods:
        calculate_co2_persons(persons_adult: float, persons_child: float, activity: MetabolicRate)\
              -> float: Calculate the total sum of generated CO2 concentration by persons.
        conversion_flow(flow: float, direction: Converting) -> float: Converts the flow \
            units for better handling.
        calculate_room_volume(area: float, height: float) -> None: Calculate the volume of \
            the room if it is not set directly.
        calculate_co2_concentration(flow_in: float, co2_generated: float) -> float: \
            Calculates the CO2 concentration in a room based on the flow rate of air entering \
            the room and the CO2 generated.
    """

    outdoor_co2: float = field(default=450)
    room_co2: float = field(default=450)
    room_volume: float = field(default=1)
    persons_adult: int = field(default=1)
    persons_child: int = field(default=0)

    def calculate_co2_persons(
        self,
        persons_adult: float,
        persons_child: float,
        activity: MetabolicRate,
    ) -> float:
        """
        Calculate the total sum of generated CO2 concentration by persons.

        Args:
            persons_adult (float): The number of adults.
            persons_child (float): The number of children.
            activity (MetabolicRate): The description of the activity.

        Returns:
            float: The total sum of generated CO2 concentration in cubic meters per hour [m³/h].
        """
        person_co2 = {"adult": 17, "child": 10}  # l/h
        met_per_person = {
            MetabolicRate.BASE: 0.8,
            MetabolicRate.RELAXED_SITTING: 1.0,
            MetabolicRate.LIGHT_SEDENTARY: 1.2,
            MetabolicRate.LIGHT_STANDING: 1.6,
            MetabolicRate.STANDING_MODERATE_ACTIVITY: 2.0,
        }  # met

        sum_co2_in = (
            met_per_person[activity] * persons_adult * person_co2["adult"]
            + met_per_person[activity] * persons_child * person_co2["child"]
        )

        return sum_co2_in

    def conversion_flow(self, flow: float, direction: Converting) -> float:
        """
        Converts the flow units for better handling.

        Args:
            flow (float): The flow rate in m³/h or m³/s.
            direction (Converting): The direction of conversion.

        Raises:
            TypeError: If the direction is not properly set or undefined.

        Returns:
            float: The converted flow rate.
        """
        if direction == Converting.M3_H_M3_S:
            return flow / 3600
        if direction == Converting.M3_S_M3_H:
            return flow * 3600

        raise TypeError("Direction is not properly set. Please check the given value")

    def calculate_room_volume(self, area: float, height: float) -> None:
        """
        Calculate the volume of the room if it is not set directly.

        Args:
            area (float): The area of the room in square meters [m²].
            height (float): The height of the room in meters [m].
        """
        self.room_volume = area * height

    def calculate_co2_concentration(
        self,
        flow_in: float,
        co2_generated: float,
    ) -> float:
        """
        Calculates the CO2 concentration in a room based on the flow rate of air \
            entering the room and the CO2 generated.

        Args:
            flow_in (float): The flow rate of air entering the room. [m³/h]
            co2_generated (float): The amount of CO2 generated in the room. [ppm]

        Returns:
            float: The CO2 concentration in the room. [ppm]
        """
        # conversion of elements for further processing
        flow_in = self.conversion_flow(flow=flow_in, direction=Converting.M3_H_M3_S)

        # air change rate
        ach = flow_in / self.room_volume

        self.room_co2 = (
            self.room_co2
            + co2_generated
            - (self.outdoor_co2 * flow_in) * math.exp(-ach)
        )
        return self.room_co2


@dataclass
class Pressure:
    """
    Represents the pressure drop calculation for a component.

    Attributes:
        component (Union[Bow, Reduction, TPiece, Duct]): The component object.
        volume_flow (float): The volume flow rate in [m³/h].
        connector (str): The connector attribute of the component.
        mean_velocity (float): The mean velocity of the connector [m/s].
        pressure_drop (float): The pressure drop for the component [Pa].

    Methods:
        __post_init__(): Performs post-initialization tasks for the class.
        _set_connector(): Sets the connector attribute based on the component type.
        set_mean_velocity(volume_flow: float): Sets the mean velocity of the connector.
        set_pressure_drop(): Calculates and sets the pressure drop for the component.
    """

    component: Union[Bow, Reduction, TPiece, Duct, Room, Flap]
    volume_flow: float
    connector: str = field(init=False)
    mean_velocity: float = field(init=False, default=0)
    pressure_drop: float = field(init=False, default=0)

    def __post_init__(self) -> None:
        """
        Performs post-initialization tasks for the class.

        This method is automatically called after the object is initialized.
        It sets the connector and calculates the mean velocity based on the volume flow.

        Parameters:
            self (object): The object instance.

        Returns:
            None
        """
        self._set_connector()
        self.set_mean_velocity(volume_flow=self.volume_flow)
        self.set_pressure_drop()

    def _set_connector(self) -> None:
        """
        Sets the connector attribute based on the component type.

        The connector attribute is set based on the component type using a mapping dictionary.
        The mapping dictionary maps each component type to the corresponding connector attribute \
            name.
        The connector attribute is then retrieved from the component object using the attribute \
            name.
        Finally, the connector attribute is assigned to the self.connector attribute.
        """

        if hasattr(self.component, "connector"):
            obj_connector = self.component.connector
        elif hasattr(self.component, "connector_a"):
            obj_connector = self.component.connector_a
        else:
            raise ValueError("Connector can't be found")

        self.connector = obj_connector

    def set_mean_velocity(self, volume_flow: float) -> None:
        """
        Sets the mean velocity of the connector based on the given volume flow.

        Args:
            volume_flow (float): The volume flow rate in cubic meters per hour.

        Returns:
            None
        """
        if self.component.componenttype == ComponentType.TPIECE:
            volume_flow = volume_flow / 2

        self.mean_velocity = (volume_flow / self.connector.area) / 3600

    def set_pressure_drop(self) -> None:
        """
        Calculates and sets the pressure drop for the component.

        The pressure drop is calculated based on the component type and the mean velocity.
        For duct components, the pressure drop is calculated using the lambda value,
        connector length, diameter, air density, and mean velocity.
        For non-duct components, the pressure drop is calculated using the zeta value,
        air density, and mean velocity.
        """
        air_density = 1.293  # kg/m³

        if self.component.componenttype == ComponentType.DUCT:
            if self.connector.shape == ComponentForm.RECTANGLED:
                diameter = (self.connector.width * self.connector.heigth) ** 0.5
            else:
                diameter = self.connector.diameter

            self.pressure_drop = (
                self.component.lambda_value
                * self.connector.length
                / 1_000
                / diameter
                * air_density
                / 2
                * self.mean_velocity**2
            )
        else:
            self.pressure_drop = (
                self.component.zeta_value * air_density / 2 * self.mean_velocity**2
            )


@dataclass
class ExportDataToAirComponents:
    """
    A class for exporting data to air components.

    Attributes:
        timestamp (pendulum.datetime): Target date for dataset.
        temperature (float): The temperature. [°C]
        volume_flow (float): The volume flow rate.[m³/h]
        pressure_drop (float): The pressure drop (default 0). [Pa]
        mass_flux (float): The mass flux (initialized automatically). [kg/s]
        density (float): The density (initialized automatically). [kg/m³]
    """

    timestamp: pendulum.datetime
    temperature: float
    volume_flow: float
    pressure_drop: float = field(default=0)
    mass_flux: float = field(init=False)
    density: float = field(init=False)

    def __post_init__(self) -> None:
        self.density = self.set_density(self.temperature)
        self.mass_flux = self.set_mass_flux(
            volume_flow=self.volume_flow, density=self.density
        )

    def __str__(self) -> str:
        msg = f"""volume_flow: {self.volume_flow:.4f} [m^3/s],\
temperature: {self.temperature:.2f} [deg C], density: {self.density:.4f} [m^3/kg]"""
        return msg

    def set_density(self, temperature: float) -> None:
        """
        Calculates and sets the density of a substance based on the given temperature.

        Args:
            temperature (float): The temperature. [°C]

        Returns:
            None
        """
        standard_pressure = 101_325  # Pa
        r_s = 287.058  # J/kgK
        temp_kelvin = temperature + 273.15  # K
        return standard_pressure / (r_s * temp_kelvin)

    def set_mass_flux(self, volume_flow: float, density: float) -> float:
        """Converts volume flow to mass flux.

        Args:
            volume_flow (float): Air flow [m³/s].
            density (float): Density of air [kg/m³].

        Returns:
            float: Mass flux [kg/s].
        """
        return volume_flow * density


# Main - Test Environment
if __name__ == "__main__":
    test = RoomLoad(
        3,
        {"window_a": 1.5},
        {"wall_a": 20},
        transmission_types={"window_a": "sheet_single"},
    )
    test2 = test.get_cooling_load_factor_radiation(
        date_time=pendulum.parse("2012-09-05T13:26:11.123789"),
        factor_type="september normal internal",
    )
    test3 = test.get_radiation_window(
        date_time=pendulum.parse("2012-09-05T13:26:11.123789"), orientation="Southwest"
    )
    test4 = test.load_radiation_windows(
        cooling_load_factor=test2,
        radiation_window=test3,
    )
    co_test = CarbonDioxid(outdoor_co2=450, room_co2=600, persons_adult=5)
    co_test.calculate_room_volume(area=50, height=2.6)
    PERSONS_ACT = 3
    sum_co2_PERSONS_ACT = float(
        co_test.calculate_co2_persons(
            persons_adult=PERSONS_ACT,
            persons_child=0,
            activity=MetabolicRate.LIGHT_SEDENTARY,
        ),
    )
    co2_concentration_test = co_test.calculate_co2_concentration(
        flow_in=500, co2_generated=sum_co2_PERSONS_ACT
    )
    # ic.ic(sum_co2_PERSONS_ACT, co2_concentration_test)
    VOLUME_FLOW = 2_500
    Bow01 = ComponentGeneral(
        component_id=1,
        orientation=ComponentOrientation.VERTICAL,
        airtype=ComponentAirType.OA,
        port_a="a",
        port_b="b",
    )
    Bow02 = ComponentRectangled(Bow01, width=600, heigth=200)
    Bow_test = Bow(Bow02, angle=90)
    pressure_test = Pressure(component=Bow_test, volume_flow=VOLUME_FLOW)
    ic.ic(pressure_test.mean_velocity, pressure_test.pressure_drop)
    Duct01 = ComponentGeneral(
        component_id=3,
        orientation=ComponentOrientation.HORIZONTAL,
        airtype=ComponentAirType.OA,
        port_a="c",
        port_b="d",
    )
    Duct02 = ComponentRectangled(Duct01, width=600, heigth=200, length=2_000)
    Duct_test = Duct(Duct02)
    pressure_test2 = Pressure(component=Duct_test, volume_flow=VOLUME_FLOW)
    ic.ic(pressure_test2.mean_velocity, pressure_test2.pressure_drop)
