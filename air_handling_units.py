# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
the ventilation units including all heaters are instantiated in this module

* HISTORY:

Date      		By	Comments
----------		---	---------------------------------------------------------


"""
# Futures
from __future__ import print_function

# Specific Imports
from dataclasses import dataclass, field
from enum import Enum, auto

# Built-in/Generic Imports
import icecream as ic

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"air_handling_units.py"


class RegisterType(Enum):
    """Register Type"""

    COOLING = auto()
    HEATING = auto()


class HeatRecoveryType(Enum):
    """Heat Recovery Type"""

    ROTARY = auto()
    PLATE = auto()
    COMPUNDSYSTEM = auto()


class UnitType(Enum):
    """Unit Type Flag"""

    FAN = auto()
    REGISTER = auto()
    HEATRECOVERY = auto()


class Conversion(Enum):
    """Conversion Type definition"""

    M3_H_M3_S = auto()
    M3_S_M3_H = auto()


@dataclass
class Fan:
    """compilaton of fan relevant propertiesi"""

    volume_flow_nominal: float
    electrical_power_nominal: float
    sfp_class: int = field(init=False)
    efficiency: float = field(init=False)
    unit_type: UnitType = field(init=False, default=UnitType.FAN)

    def __post_init__(self) -> None:
        self.volume_flow_nominal = convert_volume_flow(
            volume_flow=self.volume_flow_nominal, direction=Conversion.M3_H_M3_S
        )
        self.sfp_class = self.get_sfp_class_efficiency(
            volume_flow=self.volume_flow_nominal,
            electrical_power=self.electrical_power_nominal,
        )

    def get_sfp_class_efficiency(
        self, volume_flow: float, electrical_power: float
    ) -> int:
        """set SFP class for the fan and set the efficiency of motor unit

        Args:
            volume_flow (float): nominal volume flow [m3/s]
            electrical_power (float): nominal electrical power [W]

        Returns:
            int: SFP class
        """
        sfp_class_values = {
            300: 0,
            500: 1,
            750: 2,
            1_250: 3,
            2_000: 4,
            3_000: 5,
            4_500: 6,
            4_501: 7,
        }
        specific_power = electrical_power / volume_flow
        # choose nearest value depending on specific power
        sfp_class_key = min(sfp_class_values, key=lambda x: abs(x - specific_power))

        # calculate and set efficiency for the fan unit
        self.efficiency = min((volume_flow / electrical_power) * 1_000, 1)

        # set SFP class
        sfp_class = sfp_class_values[sfp_class_key]
        return sfp_class

    def calculate_current_power(self, volume_flow: float) -> float:
        """current power given as mean value of p_mains and efficiency calculation

        Args:
            volume_flow (float): current volume flow [m3/h]

        Returns:
            float: current electrical power [W]
        """
        # conversion of volume flow
        volume_flow = convert_volume_flow(
            volume_flow=volume_flow, direction=Conversion.M3_H_M3_S
        )

        sfp_class_values = {
            0: 300,
            1: 500,
            2: 750,
            3: 1_250,
            4: 2_000,
            5: 3_000,
            6: 4_500,
            7: 6_000,
        }

        # calculate with P_mains and the SFP class
        power_mains = volume_flow * sfp_class_values[self.sfp_class]
        # calculate with the efficiency
        power_eff = (volume_flow / self.efficiency) * 1_000
        # create mean value of previous calculation
        sum_values = [power_mains, power_eff]
        mean_power = sum(sum_values) / len(sum_values)

        return mean_power


@dataclass
class Register:
    """instance a register either heating or cooling"""

    register_type: RegisterType
    max_power: float
    unit_type: UnitType = field(init=False, default=UnitType.REGISTER)

    def calculate_current_power(
        self,
        volume_flow: float,
        sa_temperature_in: float,
        sa_temperature_out: float,
    ) -> float:
        """calculate the current power amount depending on in- and out temperatures

        Args:
            volume_flow (float): current volume flow [m³/h]
            sa_temperature_in (float): temperature in of supply air [°C]
            sa_temperature_out (float): temperature out of supply air [°C]

        Returns:
            float: calculated current power [W]
        """
        spec_heat_capacity = 1_006  # J/kgK
        density_air = 1.204  # kg/m³
        volume_flow = convert_volume_flow(
            volume_flow=volume_flow, direction=Conversion.M3_H_M3_S
        )

        if self.register_type == RegisterType.COOLING:
            return (
                volume_flow
                * density_air
                * spec_heat_capacity
                * (sa_temperature_in - sa_temperature_out)
            )

        if self.register_type == RegisterType.HEATING:
            return (
                volume_flow
                * density_air
                * spec_heat_capacity
                * (sa_temperature_out - sa_temperature_in)
            )

        raise TypeError("Please check RegisterType for register")

    def calculate_out_temperature(
        self, volume_flow: float, sa_temperature_in: float, power: float
    ) -> float:
        """calculate the out temperature depending on in temperature and power

        Args:
            volume_flow (float): current volume flow [m³/h]
            sa_temperature_in (float): temperature in of supply air [°C]
            power (float): current power [W]

        Returns:
            float: temperature out of supply air [°C]
        """
        spec_heat_capacity = 1_006  # J/kgK
        density_air = 1.204  # kg/m³
        # convert volume_flow to m³/s
        volume_flow = convert_volume_flow(
            volume_flow=volume_flow, direction=Conversion.M3_H_M3_S
        )

        # selection of register type calculation
        if self.register_type == RegisterType.COOLING:
            return sa_temperature_in - power / (
                volume_flow * density_air * spec_heat_capacity
            )

        if self.register_type == RegisterType.HEATING:
            return (
                power / (volume_flow * density_air * spec_heat_capacity)
                + sa_temperature_in
            )

        raise TypeError("Please check RegisterType for register")


@dataclass
class HeatRecovery:
    """instance heat recovery"""

    recovery_type: HeatRecoveryType
    temp_oa_nominal: float
    temp_sa_nominal: float
    temp_ra_nominal: float
    heat_exchanger_coefficient: float = field(init=False)
    unit_type: UnitType = field(init=False, default=UnitType.HEATRECOVERY)

    def __post_init__(self) -> None:
        # heat_recovery_default = {
        #     HeatRecoveryType.PLATE: [1_000, 2_000],
        #     HeatRecoveryType.ROTARY: [500, 1_500],
        #     HeatRecoveryType.COMPUNDSYSTEM: [200, 800],
        # }  # W/m²K

        self.heat_exchanger_coefficient = self.get_heat_exchanger_coefficient()

    def get_heat_exchanger_coefficient(self) -> float:
        """get the heat exchanger coefficient depending on nominal values

        Returns:
            float: heat exchanger coefficient [%]
        """
        return (self.temp_sa_nominal - self.temp_oa_nominal) / (
            self.temp_ra_nominal - self.temp_oa_nominal
        )

    def calculate_current_power(
        self, volume_flow: float, oa_temperature: float, sa_temperature: float
    ) -> float:
        """power of the heat exchanger

        Args:
            volume_flow (float): flow [m³/h]
            oa_temperature (float): outside air temperature [°C]
            sa_temperature (float): supply air temperature [°C]

        Returns:
            float: current power [W]
        """
        spec_heat_capacity = 1_006  # J/kgK
        density_air = 1.204  # kg/m³

        # converting volume_flow to m³/s
        volume_flow = convert_volume_flow(
            volume_flow=volume_flow, direction=Conversion.M3_H_M3_S
        )
        return (
            volume_flow
            * density_air
            * spec_heat_capacity
            * (sa_temperature - oa_temperature)
        )

    def calculate_sa_temperature(
        self, ra_temperature: float, oa_temperature: float
    ) -> float:
        """supply air temperature after heat recovery

        Args:
            ra_temperature (float): return air temperature [°C]
            oa_temperature (float): outside air temperature [°C]

        Returns:
            float: supply air temperature [°C]
        """
        return (
            self.heat_exchanger_coefficient * (ra_temperature - oa_temperature)
            + oa_temperature
        )


def convert_volume_flow(volume_flow: float, direction: Conversion) -> float:
    """conversion of the volume

    Args:
         volume_flow (float): input volume flow for conversion

     Returns:
         float: converted volume flow
    """

    if direction == Conversion.M3_H_M3_S:
        return volume_flow / 3600
    if direction == Conversion.M3_S_M3_H:
        return volume_flow * 3600

    raise TypeError("Direction is not properly set. Please check the given value")


# Main - Test Environment
if __name__ == "__main__":
    # Fan Datasheet
    # https://global.heliosventilatoren.de/mediadata/product/datasheet/Helios_HK_6.0_D_1023_452-453.pdf
    VOLUME_FLOW_ACT = 7_600
    ventilation = Fan(
        volume_flow_nominal=VOLUME_FLOW_ACT, electrical_power_nominal=2_810
    )
    # ic.ic(
    #     test.calculate_current_power(volume_flow=7_600 / 2),
    #     test.electrical_power_nominal / 2,
    # )
    heat_recovery = HeatRecovery(
        recovery_type=HeatRecoveryType.PLATE,
        temp_oa_nominal=-13,
        temp_sa_nominal=16,
        temp_ra_nominal=22,
    )
    OA_TEMPERATURE_ACT = 8
    SA_TEMPERATURE_ACT = 22
    sa_temperate_act = heat_recovery.calculate_sa_temperature(
        ra_temperature=SA_TEMPERATURE_ACT, oa_temperature=OA_TEMPERATURE_ACT
    )
    power_hr_test = heat_recovery.calculate_current_power(
        volume_flow=VOLUME_FLOW_ACT,
        oa_temperature=OA_TEMPERATURE_ACT,
        sa_temperature=sa_temperate_act,
    )
    ic.ic(heat_recovery.heat_exchanger_coefficient, sa_temperate_act, power_hr_test)
    cooling_register = Register(register_type=RegisterType.COOLING, max_power=20_000)
    cooling_power = cooling_register.calculate_current_power(
        volume_flow=VOLUME_FLOW_ACT, sa_temperature_in=24, sa_temperature_out=19
    )
    cooling_temp_sa = cooling_register.calculate_out_temperature(
        volume_flow=VOLUME_FLOW_ACT, sa_temperature_in=24, power=cooling_power
    )
    ic.ic(cooling_register, cooling_power, cooling_temp_sa)
    heating_register = Register(register_type=RegisterType.HEATING, max_power=15_000)
    heating_power = heating_register.calculate_current_power(
        volume_flow=VOLUME_FLOW_ACT, sa_temperature_in=19, sa_temperature_out=24
    )
    heating_temp_sa = heating_register.calculate_out_temperature(
        volume_flow=VOLUME_FLOW_ACT, sa_temperature_in=19, power=cooling_power
    )
    ic.ic(heating_register, heating_power, heating_temp_sa)
