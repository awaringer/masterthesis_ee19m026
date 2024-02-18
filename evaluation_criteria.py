# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
This module is used to evaluate the predicted mean value of votes (PMV) and the 
predicted percentage of dissatisfaction (PPD). This is done using input parameters 
from other modules. The module is also used to evaluate the perceived air quality.

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
10-12-2023		AW	evaluation of the results and adaptation of the findings
09-12-2023		AW	creation


"""
# Futures
from __future__ import print_function

# Built-in/Generic Imports
import math

# Specific Imports
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict
from icecream import ic

# Libs
import pandas as pd

# Own modules
from building_information import Room

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"pmv_ppd.py"


class PersonType(Enum):
    """An enumeration representing different types of persons."""

    ADULT = auto()
    CHILD = auto()


class ActivityType(Enum):
    """
    Enumeration representing different activity types.

    Attributes:
        SITTING: Represents sitting activity.
        SITTING_SMOKER_LIGHT: Represents sitting activity as a light smoker.
        SITTING_SMOKER_MEDIUM: Represents sitting activity as a medium smoker.
        SITTING_SMOKER_HEAVY: Represents sitting activity as a heavy smoker.
        LOW_ACTIVITY: Represents low physical activity.
        MEDIUM_ACTIVITY: Represents medium physical activity.
        HIGH_ACTIVITY: Represents high physical activity.
    """

    SITTING = auto()
    SITTING_SMOKER_LIGHT = auto()
    SITTING_SMOKER_MEDIUM = auto()
    SITTING_SMOKER_HEAVY = auto()
    LOW_ACTIVITY = auto()
    MEDIUM_ACTIVITY = auto()
    HIGH_ACTIVITY = auto()
    CHILD = auto()


class RoomType(Enum):
    """
    Enumeration representing different types of rooms.
    """

    OFFICE = auto()
    CLASSROOM = auto()
    KINDERGARTEN = auto()
    MEETING_ROOM = auto()


@dataclass
class ThermalComfort:
    """class for calculation of pmv and ppd at a specific point of time

    Args:
        clothing (float): clo
        metablic_work (float): W/m2
        external_work (float): usually 0, W*m2
        air_temp (float): °C
        mean_radiant_temp (float): °C
        air_velocity (float): m/s
        rel_humidity (float): %, Notation from 0 to 1!

    Returns:
        pmv (float): dimensionless
        ppd (float): % Notation from 0 to 100!
    """

    air_temp: float  # °C
    mean_radiant_temp: float  # °C
    air_velocity: float  # m/s
    rel_humidity: float  # %
    clothing: float = field(default=0.7)  # clo
    metablic_work: float = field(default=70)  # W/m2
    external_work: float = field(default=0)  # W/m2
    water_vapour_pressure: float = field(init=False)  # Pa
    pmv: float = field(init=False)  # dimensionless
    ppd: float = field(init=False)  # %

    def __post_init__(self) -> None:
        self.water_vapour_pressure = self.calculate_water_vapor_pressure()
        self.pmv = self.calculate_pmv()
        self.ppd = self.calculate_ppd()

    def __str__(self) -> str:
        msg = f"""-----------------------------------------------------------------------
Predicted Mean Vote (PMV): {self.pmv}
Predicted Percent of Dissatisfied (PPD): {self.ppd}
"""

        return msg

    def calculate_water_vapor_pressure(self) -> float:
        """Calculation of water vapor pressure in the air based on temperature and relative humidity

        Returns:
            float: water vapor pressure in the air in Pa
        """
        return self.rel_humidity * math.exp(
            16.6536 - 4030.183 / ((self.air_temp + 273.15) + 235)
        )

    def calculate_surface_temp_clothing(
        self,
        ins_clothing: float,
        clothing_factor: float,
        internal_heat_body: float,
        mean_radiant_temp_kelvin: float,
    ) -> float:
        """This method is used to calculate the surface temperature of clothing,
        which also takes into account the internal heat development of the human body

        Args:
            ins_clothing (float): clothing insulation in m2*K/W
            clothing_factor (float): clothing factor, dimensionless
            internal_heat_body (float): sum of metabolic rate and external work rate in W*m2
            mean_radiant_temp_kelvin (float): radiant temperature in kelvin

        Returns:
            float: surface clothing temperature in K
            float: offset factor in K
            float: convective heat transfer coefficient in W/m2*K
        """
        air_speed = max(self.air_velocity, 0.1)
        heat_coeff = 12.1 * math.sqrt(air_speed)
        air_temp_kelvin = self.air_temp + 273.15

        surface_temp_clothing = air_temp_kelvin + (35.5 - self.air_temp) / (
            3.5 * (6.45 * (ins_clothing + 0.1))
        )

        calculation_term = []
        calculation_term.append(ins_clothing * clothing_factor)
        calculation_term.append(calculation_term[0] * 3.96)
        calculation_term.append(calculation_term[0] * 100)
        calculation_term.append(calculation_term[0] * air_temp_kelvin)
        calculation_term.append(
            308.7
            - 0.028 * internal_heat_body
            + calculation_term[1] * (mean_radiant_temp_kelvin / 100) ** 4
        )

        factor_new = surface_temp_clothing / 100
        factor_stored = factor_new
        delta_alpha = 0.00015

        while True:
            factor_stored = (factor_stored + factor_new) / 2
            heat_coeff_convection = (
                2.38 * abs(100 * factor_stored - air_temp_kelvin) ** 0.25
            )
            heat_coeff = (
                heat_coeff
                if heat_coeff > heat_coeff_convection
                else heat_coeff_convection
            )
            factor_new = (
                calculation_term[4]
                + calculation_term[3] * heat_coeff
                - calculation_term[1] * factor_stored**4
            ) / (100 + calculation_term[2] * heat_coeff)

            if abs(factor_new - factor_stored) <= delta_alpha:
                break

        surface_temp_clothing = 100 * factor_new - 273.15

        return surface_temp_clothing, factor_new, heat_coeff

    def calculate_pmv(self) -> float:
        """calculation of the PVM value for the evaluation of the PPD

        Returns:
            float: predicted mean vote (PVM), dimensionless
        """
        ins_clothing = 0.155 * self.clothing
        int_heat_body = self.metablic_work - self.external_work
        clothing_factor = 1.05 + 0.645 * ins_clothing

        mean_radiant_temp_kelvin = self.mean_radiant_temp + 273.15

        (
            surface_temperature_clothing,
            offset_factor,
            heat_coeff,
        ) = self.calculate_surface_temp_clothing(
            ins_clothing,
            clothing_factor,
            int_heat_body,
            mean_radiant_temp_kelvin,
        )

        heat_loss_skin = 3.05 * 0.001 * (5733 - 6.99 - int_heat_body)
        heat_loss_sweating = (
            0.42 * (int_heat_body - 58.15) if int_heat_body > 58.15 else 0
        )
        heat_loss_latent_respiration = (
            1.7 * 0.00001 * self.metablic_work * (5867 - self.water_vapour_pressure)
        )
        heat_loss_dry_respiration = 0.0014 * self.metablic_work * (34 - self.air_temp)
        heat_loss_radiation = (
            3.96
            * clothing_factor
            * (offset_factor**4 - (mean_radiant_temp_kelvin / 100) ** 4)
        )
        heat_loss_convection = (
            clothing_factor
            * heat_coeff
            * (surface_temperature_clothing - self.air_temp)
        )

        termal_sensation = 0.303 * math.exp(-0.036 * self.metablic_work) + 0.028
        return termal_sensation * (
            int_heat_body
            - heat_loss_skin
            - heat_loss_sweating
            - heat_loss_latent_respiration
            - heat_loss_dry_respiration
            - heat_loss_radiation
            - heat_loss_convection
        )

    def calculate_ppd(self) -> float:
        """calculation of the PPD value for further processing and decisionmaking

        Returns:
            float: predicted percentage of dissatisfied (PPD) in %
        """
        return 100 - 95 * math.exp(-0.03353 * self.pmv**4 - 0.2179 * self.pmv**2)


@dataclass
class AirQualityComfort:
    """
    Class representing the air quality comfort.

    Attributes:
        persons (Dict[PersonType, float]): A dictionary mapping person types to their count.
        activity (Dict[ActivityType, float]): A dictionary mapping activity types to their count.
        room_type (RoomType): The type of the room.
        room_data (Room): The data of the room.

    Methods:
        user_contamination_load(self) -> float: Calculates the user contamination load in the room.
        room_contamination_load(self) -> float: Calculates the contamination load of the room.
        perceived_air_quality(self, user_contamination: float, room_contamination: float, \
            volume_flow: float) -> float: Calculates the perceived air quality.
        percentage_dissatisfied(self, perceived_air_quality: float) -> float: \
            Calculates the percentage of dissatisfied individuals.
    """

    persons: Dict[PersonType, float]
    activity: Dict[ActivityType, float]
    room_type: RoomType
    room_data: Room

    def user_contamination_load(self) -> float:
        """Calculation of the user contamination load in the room

        Returns:
            float: user contamination load in the room in [olf]
        """
        user_contamination_activity = {
            ActivityType.SITTING: 1,
            ActivityType.SITTING_SMOKER_LIGHT: 2,
            ActivityType.SITTING_SMOKER_MEDIUM: 3,
            ActivityType.SITTING_SMOKER_HEAVY: 6,
            ActivityType.LOW_ACTIVITY: 4,
            ActivityType.MEDIUM_ACTIVITY: 10,
            ActivityType.HIGH_ACTIVITY: 20,
            ActivityType.CHILD: 1.3,
        }

        contamination_load = 0

        if self.persons is not None:
            for activity, count in self.activity.items():
                contamination_load += count * user_contamination_activity[activity]

        return contamination_load

    def room_contamination_load(self) -> float:
        """
        Calculates the contamination load of a room based on its area and room type.

        Returns:
            The contamination load of the room as a float value. [olf]
        """
        room_contamination_area = {
            RoomType.OFFICE: 0.3,
            RoomType.CLASSROOM: 0.3,
            RoomType.KINDERGARTEN: 0.4,
            RoomType.MEETING_ROOM: 0.5,
        }

        contamination_load = (
            self.room_data.area * room_contamination_area[self.room_type]
        )

        return contamination_load

    def perceived_air_quality(
        self,
        user_contamination: float,
        room_contamination: float,
        volume_flow: float,
    ) -> float:
        """
        Calculates the perceived air quality based on user contamination, \
            room contamination, and volume flow.

        Parameters:
        user_contamination (float): The level of contamination caused by the user. [olf]
        room_contamination (float): The level of contamination in the room. [olf]
        volume_flow (float): The volume flow of air in the room. [m³/h]

        Returns:
        float: The perceived air quality. [dezipol]

        """
        return 10 * (user_contamination + room_contamination) / volume_flow

    def percentage_dissatisfied(self, perceived_air_quality: float) -> float:
        """
        Calculates the percentage of dissatisfied individuals based on the perceived air quality.

        Args:
            perceived_air_quality (float): The perceived air quality, ranging from 0 to 1.

        Returns:
            float: The percentage [0...100] of dissatisfied individuals. [%]

        """
        return 395 * math.exp(-3.25 * perceived_air_quality**-0.25)


if __name__ == "__main__":
    PERSON = {PersonType.ADULT: 3, PersonType.CHILD: 2}
    ACTIVITY = {ActivityType.SITTING: 3, ActivityType.CHILD: 2}
    test_room = Room(room_number="R1", persons=5, height=2.7)
    test_room.set_area(length=5, width=5)
    test_room.set_volume_flow(room_volume=test_room.get_volume(), air_change_rate=1)
    test_aq = AirQualityComfort(
        persons=PERSON,
        activity=ACTIVITY,
        room_type=RoomType.OFFICE,
        room_data=test_room,
    )
    user_load = test_aq.user_contamination_load()
    room_Load = test_aq.room_contamination_load()
    perceived_air_quality_act = test_aq.perceived_air_quality(
        user_contamination=user_load,
        room_contamination=room_Load,
        volume_flow=test_room.volume_flow,
    )
    perc_diss = test_aq.percentage_dissatisfied(
        perceived_air_quality=perceived_air_quality_act
    )
    ic(perc_diss)
    Test1 = ThermalComfort(
        air_temp=22,
        mean_radiant_temp=22,
        air_velocity=0.1,
        rel_humidity=0.6,
        metablic_work=1.2 * 58.15,
        clothing=0.5,
    )
    Test2 = ThermalComfort(
        air_temp=27,
        mean_radiant_temp=27,
        air_velocity=0.1,
        rel_humidity=0.6,
        metablic_work=1.2 * 58.15,
        clothing=0.5,
    )
    Test3 = ThermalComfort(
        air_temp=27,
        mean_radiant_temp=27,
        air_velocity=0.3,
        rel_humidity=0.6,
        metablic_work=1.2 * 58.15,
        clothing=0.5,
    )
    Test4 = ThermalComfort(
        air_temp=23.5,
        mean_radiant_temp=25.5,
        air_velocity=0.1,
        rel_humidity=0.6,
        metablic_work=1.2 * 58.15,
        clothing=0.5,
    )
    Test5 = ThermalComfort(
        air_temp=23.5,
        mean_radiant_temp=25.5,
        air_velocity=0.3,
        rel_humidity=0.6,
        metablic_work=1.2 * 58.15,
        clothing=0.5,
    )
    Test6 = ThermalComfort(
        air_temp=19,
        mean_radiant_temp=19,
        air_velocity=0.1,
        rel_humidity=0.4,
        metablic_work=1.2 * 58.15,
        clothing=1,
    )
    Test7 = ThermalComfort(
        air_temp=23.5,
        mean_radiant_temp=23.5,
        air_velocity=0.1,
        rel_humidity=0.4,
        metablic_work=1.2 * 58.15,
        clothing=1,
    )
    Test8 = ThermalComfort(
        air_temp=23.5,
        mean_radiant_temp=23.5,
        air_velocity=0.3,
        rel_humidity=0.4,
        metablic_work=1.2 * 58.15,
        clothing=1,
    )
    Test9 = ThermalComfort(
        air_temp=23,
        mean_radiant_temp=21,
        air_velocity=0.1,
        rel_humidity=0.4,
        metablic_work=1.2 * 58.15,
        clothing=1,
    )
    Test10 = ThermalComfort(
        air_temp=23,
        mean_radiant_temp=21,
        air_velocity=0.3,
        rel_humidity=0.4,
        metablic_work=1.2 * 58.15,
        clothing=1,
    )
    Test11 = ThermalComfort(
        air_temp=22,
        mean_radiant_temp=22,
        air_velocity=0.1,
        rel_humidity=0.6,
        metablic_work=1.6 * 58.15,
        clothing=0.5,
    )
    Test12 = ThermalComfort(
        air_temp=27,
        mean_radiant_temp=27,
        air_velocity=0.1,
        rel_humidity=0.6,
        metablic_work=1.6 * 58.15,
        clothing=0.5,
    )
    Test13 = ThermalComfort(
        air_temp=27,
        mean_radiant_temp=27,
        air_velocity=0.3,
        rel_humidity=0.6,
        metablic_work=1.6 * 58.15,
        clothing=0.5,
    )
    TestObjects = [
        Test1,
        Test2,
        Test3,
        Test4,
        Test5,
        Test6,
        Test7,
        Test8,
        Test9,
        Test10,
        Test11,
        Test12,
        Test13,
    ]
    clms = [
        "Luftemperatur",
        "Strahlungstemperatur",
        "Luftgeschwindigkeit",
        "rel. Feuchte",
        "Energieumsatz",
        "Bekleidungsisoluation",
        "PMV_kalk",
        "PPD_kalk",
    ]
    PMV_Soll = [
        -0.75,
        0.77,
        0.44,
        -0.01,
        -0.55,
        -0.60,
        0.5,
        0.12,
        0.05,
        -0.16,
        0.05,
        1.17,
        0.95,
    ]
    PPD_Soll = [17, 17, 9, 5, 11, 13, 10, 5, 5, 6, 5, 34, 24]
    temp, radiation, vel, rh, met, clo, pmv, ppd = ([] for i in range(len(clms)))
    for x in TestObjects:
        temp.append(x.air_temp)
        radiation.append(x.mean_radiant_temp)
        vel.append(x.air_velocity)
        rh.append(x.rel_humidity)
        met.append(x.metablic_work)
        clo.append(x.clothing)
        pmv.append(x.pmv)
        ppd.append(x.ppd)
    data = list(zip(temp, radiation, vel, rh, met, clo, pmv, ppd))
    df = pd.DataFrame(data, columns=clms)
    df["PMV_Soll"] = PMV_Soll
    df["PPD_Soll"] = PPD_Soll
    df["PMV_diff"] = df["PMV_kalk"] - df["PMV_Soll"]
    df["PPD_diff"] = df["PPD_kalk"] - df["PPD_Soll"]
    df.index = df.index + 1
    table_plt = df[
        [
            "Luftemperatur",
            "Energieumsatz",
            "Luftgeschwindigkeit",
            "PMV_kalk",
            "PPD_kalk",
            "PMV_Soll",
            "PPD_Soll",
            "PMV_diff",
            "PPD_diff",
        ]
    ]
    ic(table_plt)

    ic(
        f'PMV diff: {df["PMV_diff"].mean()}; \
        PMV min: {df["PMV_diff"].min()}; \
        PMV max: {df["PMV_diff"].max()}'
    )
    ic(
        f'PPD diff: {df["PPD_diff"].mean()}; \
        PPD min: {df["PPD_diff"].min()}; \
        PPD max: {df["PPD_diff"].max()}'
    )
