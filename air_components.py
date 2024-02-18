# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
all pipe duct components are instantiated in this module

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
7-01-2024		AW	refactoring code
x-12-2023		AW	
x-12-2023		AW	


"""
# Futures
from __future__ import print_function

# Built-in/Generic Imports
import math

# Specific Imports
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Union, List
from icecream import ic

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"air_components.py"


class ComponentForm(Enum):
    """component form enum class"""

    RECTANGLED = auto()
    CIRCLED = auto()


class ComponentType(Enum):
    """component type enum class"""

    DUCT = auto()
    BOW = auto()
    REDUCTION = auto()
    TPIECE = auto()
    AIRTERMINAL = auto()
    ROOM = auto()
    FLAP = auto()
    FAN = auto()


class ComponentOrientation(Enum):
    """component orientation enum class"""

    VERTICAL = auto()
    HORIZONTAL = auto()


class ReductionType(Enum):
    """reduction either extending or narrowing"""

    EXTENSION = auto()
    NARROWING = auto()


class ComponentAirType(Enum):
    """air type enums for assigning
    EA exhaust air / Fortluft "FOL"
    OA outside air / Außenluft "AUL"
    SA supply air / Zuluft "ZUL"
    RA return air / Abluft "ABL"
    """

    EA = "FOL"
    OA = "AUL"
    SA = "ZUL"
    RA = "ABL"


@dataclass
class ComponentGeneral:
    """General information inheriting to subclasses circled and rectangled.

    Attributes:
        component_id (str): The ID of the component.
        orientation (ComponentOrientation): The orientation of the component.
        airtype (ComponentAirType): The air type of the component.
        port_a (str): The port A of the component.
        port_b (str): The port B of the component.
    """

    component_id: str
    orientation: ComponentOrientation
    airtype: ComponentAirType
    port_a: str
    port_b: str

    def __str__(self) -> str:
        """Return a string representation of the ComponentGeneral object."""
        msg = f"""-----------------------------------------------------------------------
id: {self.component_id}
Port A: {self.port_a}, Port B: {self.port_b}"""

        return msg


@dataclass
class ComponentCircled:
    """
    Class for containing information of a circled component.

    Args:
        general (ComponentGeneral): The general information of the component.
        length (float, optional): The length of the component in millimeters. Defaults to 0.
        diameter (int, optional): The diameter of the component in millimeters. Defaults to 0.
        area (float, optional): The area of the component in square meters. Defaults to 0.
        shape (ComponentForm, optional): The shape form of the component. Defaults to Compone\
            ntForm.CIRCLED.
    """

    general: ComponentGeneral
    length: float = field(default=0)
    diameter: int = field(default=0)
    area: float = field(default=0)
    shape: ComponentForm = ComponentForm.CIRCLED

    def __post_init__(self) -> None:
        """
        This method is called after the object is initialized.
        It calculates the area of the air component.
        """
        self._calculate_area()

    def __str__(self) -> str:
        """
        Returns a string representation of the AirComponent object.

        Returns:
            str: A string containing information about the AirComponent object.
        """
        msg = f"""{self.general}
    shape form: {self.shape}
    length: {self.length:.0f} [mm],
    diameter: {self.diameter:.0f} [mm]
    area: {self.area:.2f} [m^2]"""

        return msg

    def _calculate_area(self) -> None:
        """calculate circled area in m2"""
        self.area = (((self.diameter / 2) ** 2) * math.pi) / 1_000_000


@dataclass
class ComponentRectangled:
    """Class for containing information of a rectangled component.

    Attributes:
        general (ComponentGeneral): The general information of the component.
        length (float): The length of the component in millimeters.
        width (int): The width of the component in millimeters.
        heigth (int): The height of the component in millimeters.
        area (float): The area of the component in square meters.
        shape (ComponentForm): The shape form of the component (always ComponentForm.RECTANGLED).

    Methods:
        __post_init__(): This method is called after the object has been initialized. .\
            It calculates the area of the air component.
        __str__(): Returns a string representation of the object.
        _calculate_area(): Calculate the area of the rectangle in square meters.

    """

    general: ComponentGeneral
    length: float = field(default=0)
    width: int = field(default=0)
    heigth: int = field(default=0)
    area: float = field(default=0)
    shape: ComponentForm = ComponentForm.RECTANGLED

    def __post_init__(self) -> None:
        """
        This method is called after the object has been initialized.
        It calculates the area of the air component.
        """
        self._calculate_area()

    def __str__(self) -> str:
        """
        Returns a string representation of the object.

        Returns:
            str: A string representation of the object.
        """
        msg = f"""{self.general}
    shape form: {self.shape}
    length: {self.length:.0f} [mm]
    width a: {self.width:.0f} [mm], heigth a: {self.heigth:.0f} [mm]
    area: {self.area:.2f} [m^2]"""

        return msg

    def _calculate_area(self) -> None:
        """
        Calculate the area of the rectangle in square meters.

        This method calculates the area of the rectangle based on its width and height.
        The result is stored in the `area` attribute of the object.

        Returns:
            None
        """
        self.area = (self.width * self.heigth) / 1_000_000


@dataclass
class Bow:
    """Component class of type bow with inherited class type of circled or rectangled.

    Args:
        connector (Union[ComponentCircled, ComponentRectangled]): The connector of the bow.
        angle (float): The angle of the bow in degrees.
    """

    connector: Union[ComponentCircled, ComponentRectangled]
    angle: float
    componenttype: ComponentType = ComponentType.BOW
    zeta_value: float = field(init=False)
    _angle_rad: float = field(init=False)

    def __post_init__(self):
        """
        Performs post-initialization tasks for the class.
        """
        self._set_length()
        self._set_zeta_value()

    def __str__(self) -> str:
        """
        Returns a string representation of the AirComponent object.

        The string includes the connector, angle in degrees and radians, zeta value, and shape type.

        Returns:
            str: A string representation of the AirComponent object.
        """
        msg = f"""{self.connector}
    angle: {self.angle:.0f} [degree], angle radiant: {self._angle_rad:.4f} [rad]
    zeta value: {self.zeta_value:.4f} [-]
    shape type: {self.componenttype}"""
        return msg

    def _set_length(self) -> None:
        """
        Sets the length of the connector based on its shape and orientation.

        The length is calculated using the angle of the connector and the dimensions
        of the connector's shape (width, height, or diameter). The calculated length
        is rounded to the nearest whole number.

        Raises:
            TypeError: If the shape information of the connector is invalid.
        """
        self._angle_rad = math.radians(self.angle / 2)

        if (
            self.connector.shape is ComponentForm.RECTANGLED
            and self.connector.general.orientation is ComponentOrientation.HORIZONTAL
        ):
            self.connector.length = round(
                math.tan(self._angle_rad) * self.connector.width, 0
            )

        elif (
            self.connector.shape is ComponentForm.RECTANGLED
            and self.connector.general.orientation is ComponentOrientation.VERTICAL
        ):
            self.connector.length = round(
                math.tan(self._angle_rad) * self.connector.heigth, 0
            )

        elif self.connector.shape is ComponentForm.CIRCLED:
            self.connector.length = round(
                math.tan(self._angle_rad) * self.connector.diameter, 0
            )

        else:
            raise TypeError(f"Cant process shape information {TypeError}")

    def _get_factor_r_d(self) -> float:
        """
        Calculate the factor r/d based on the shape and orientation of the connector.

        Returns:
            float: The calculated factor r/d.
        """
        if (
            self.connector.shape is ComponentForm.RECTANGLED
            and self.connector.general.orientation is ComponentOrientation.HORIZONTAL
        ):
            _radius = self.connector.length * math.cos(
                self._angle_rad
            ) + self.connector.width * math.sin(self._angle_rad)
            _factor_r_d = _radius / self.connector.width

        elif (
            self.connector.shape is ComponentForm.RECTANGLED
            and self.connector.general.orientation is ComponentOrientation.VERTICAL
        ):
            _radius = self.connector.length * math.cos(
                self._angle_rad
            ) + self.connector.heigth * math.sin(self._angle_rad)
            _factor_r_d = _radius / self.connector.heigth

        elif self.connector.shape is ComponentForm.CIRCLED:
            _radius = self.connector.length * math.cos(
                self._angle_rad
            ) + self.connector.diameter * math.sin(self._angle_rad)
            _factor_r_d = _radius / self.connector.diameter

        else:
            raise TypeError(f"Cant process shape information {TypeError}")

        return _factor_r_d

    def _set_zeta_value(self) -> None:
        """
        Sets the value of the zeta parameter based on the shape of the connector.

        If the shape is rectangular, the zeta value is determined using a lookup table
        based on the factor_r_d value. If the shape is circular, a different lookup table
        is used. If the shape is neither rectangular nor circular, a TypeError is raised.

        Raises:
            TypeError: If the shape information is not recognized.

        Returns:
            None
        """
        if self.connector.shape is ComponentForm.RECTANGLED:
            zeta_rectangle_bow = {0: 1.4, 0.2: 0.7, 0.4: 0.6, 0.6: 0.7, 0.8: 1.1}
            factor_r_d = self._get_factor_r_d()
            _, self.zeta_value = min(
                zeta_rectangle_bow.items(), key=lambda x: abs(factor_r_d - x[0])
            )

        elif self.connector.shape is ComponentForm.CIRCLED:
            zeta_round_bow = {
                0.50: 0.9,
                0.75: 0.43,
                1.00: 0.33,
                1.50: 0.24,
                2.00: 0.19,
                3.00: 0.17,
                4.00: 0.15,
            }
            factor_r_d = self._get_factor_r_d()
            _, self.zeta_value = min(
                zeta_round_bow.items(), key=lambda x: abs(factor_r_d - x[0])
            )
        else:
            raise TypeError(f"Cant process shape information {TypeError}")


@dataclass
class Duct:
    """
    Represents a duct component.

    Args:
    - connector (Union[ComponentCircled, ComponentRectangled]): The connector of the duct.
    - mean_velocity (float, optional): The mean velocity of the air in m/s. Default is 0.01.
    - componenttype (ComponentType, optional): The type of the component. Default is \
        ComponentType.DUCT.

    Attributes:
    - connector (Union[ComponentCircled, ComponentRectangled]): The connector of the duct.
    - mean_velocity (float): The mean velocity of the air in m/s.
    - componenttype (ComponentType): The type of the component.
    - lambda_value (float): The lambda value of the duct.

    Methods:
    - __post_init__(): Perform post-initialization tasks for the duct component.
    - __str__(): Returns a string representation of the duct component.
    - _get_diameter(): Calculate the diameter parameter for processing calculation of \
        Reynolds number.
    - _get_reynolds(mean_velocity: float, diameter: float): Calculate the Reynolds number.
    - set_lambda(reynolds_number: float): Calculate the lambda value.
    """

    connector: Union[ComponentCircled, ComponentRectangled]
    mean_velocity: float = field(default=0.01)
    componenttype: ComponentType = ComponentType.DUCT
    lambda_value: float = field(init=False)

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks for the duct component.

        This method calculates the diameter, Reynolds number, and sets the lambda value \
            for the duct component.

        Parameters:
        - self: The duct component object.

        Returns:
        - None
        """
        diameter = self._get_diameter()
        reynolds_number = self._get_reynolds(self.mean_velocity, diameter)
        self.set_lambda(reynolds_number)

    def __str__(self) -> str:
        """
        Returns a string representation of the duct component.

        The string includes the connector, mean velocity, lambda value, and shape type.

        Returns:
            str: A string representation of the duct component.
        """
        msg = f"""{self.connector}
    {self.connector}
    mean velocity: {self.mean_velocity:.4f} [m/s]
    lambda value: {self.lambda_value:.4f} [-]
    shape type: {self.componenttype}"""
        return msg

    def _get_diameter(self) -> float:
        """Calculate a specific diameter parameter for processing calculation
        of Reynolds number.

        Raises:
            TypeError: If the object has an improper shape type (circled or rectangled).

        Returns:
            float: The diameter dimension.
        """
        if self.connector.shape is ComponentForm.RECTANGLED:
            a_factor = self.connector.width * self.connector.width
            p_factor = 2 * self.connector.width + 2 * self.connector.width
            return 4 * (a_factor / p_factor)

        if self.connector.shape is ComponentForm.CIRCLED:
            return self.connector.diameter

        raise TypeError(f"Can't process shape information {TypeError}")

    def _get_reynolds(self, mean_velocity: float, diameter: float) -> float:
        """Calculate the Reynolds number.

        This method calculates the Reynolds number based on the mean velocity and diameter.

        Args:
            mean_velocity (float): The mean velocity in m/s.
            diameter (float): The diameter in mm.

        Returns:
            float: The Reynolds number.

        """
        viscosity = 13.3  # mm^2/s - constant
        return mean_velocity * diameter / viscosity

    def set_lambda(self, reynolds_number: float) -> None:
        """Calculate the lambda value.

        Args:
            reynolds_number (float): The dimensionless Reynolds number.

        Returns:
            None: This method does not return anything.
        """
        if reynolds_number < 2300:
            self.lambda_value = 0.3164 / (reynolds_number**0.25)
        else:
            self.lambda_value = 64 / reynolds_number


@dataclass
class Reduction:
    """
    Represents a component of type reduction with inherited class type of circled or rectangled.

    Args:
        connector_a (Union[ComponentCircled, ComponentRectangled]): The first connector of the \
            reduction component.
        connector_b (Union[ComponentCircled, ComponentRectangled]): The second connector of the \
            reduction component.
        reductiontype (ReductionType): The type of reduction (NARROWING or EXTENSION).
    """

    connector_a: Union[ComponentCircled, ComponentRectangled]
    connector_b: Union[ComponentCircled, ComponentRectangled]
    reductiontype: ReductionType
    componenttype: ComponentType = ComponentType.REDUCTION
    zeta_value: float = field(init=False)

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks for the object.
        This method is automatically called after the object is initialized.
        """
        self.get_zeta_value()

    def __str__(self) -> str:
        """
        Returns a string representation of the AirComponent object.

        If the shape of connector_a is RECTANGLED, the string includes the following information:
        - connector_a
        - width b
        - height b
        - area b
        - zeta value
        - shape type

        If the shape of connector_a is not RECTANGLED, the string includes the \
            following information:
        - connector_a
        - diameter b
        - area b
        - zeta value
        - shape type

        Returns:
            str: A string representation of the AirComponent object.
        """
        if self.connector_a.shape is ComponentForm.RECTANGLED:
            msg = f"""{self.connector_a}
    width b: {self.connector_b.width:.0f} [mm], heigth b: {self.connector_b.heigth:.0f} [mm]
    area b: {self.connector_b.area:.2f} [mm^2]
    zeta value: {self.zeta_value:.4f} [-]
    shape type: {self.componenttype}"""

        else:
            msg = f"""{self.connector_a}
    diameter b: {self.connector_b.diameter:.0f} [mm]
    area b: {self.connector_b.area:.2f} [mm^2]
    zeta value: {self.zeta_value:.4f} [-]
    shape type: {self.componenttype}"""

        return msg

    def _get_area_factor(self) -> float:
        """Calculate the area factor based on the reduction type.

        The area factor is calculated as follows:
        - For Narrowing: A2/A1
        - For Extension: A1/A2

        Raises:
            TypeError: If the reduction type is not defined.

        Returns:
            float: The calculated area factor, which is dimensionless.
        """
        if self.reductiontype == ReductionType.NARROWING:
            return self.connector_b.area / self.connector_a.area

        if self.reductiontype == ReductionType.EXTENSION:
            return self.connector_a.area / self.connector_b.area

        raise TypeError("Cannot process reduction type information.")

    def get_zeta_value(self) -> None:
        """set the zeta value for the reduction component

        Raises:
            TypeError: if reduction type is not defined
        """
        area_factor = self._get_area_factor()

        if self.reductiontype == ReductionType.NARROWING:
            zeta_narrowing = {
                0.2: 0.75,
                0.4: 0.77,
                0.5: 0.79,
                0.6: 0.82,
                0.7: 0.85,
                0.9: 0.94,
                1: 1,
            }
            _, self.zeta_value = min(
                zeta_narrowing.items(), key=lambda x: abs(area_factor - x[0])
            )

        elif self.reductiontype == ReductionType.EXTENSION:
            zeta_extension = {
                0.4: 0.125,
                0.5: 0.11,
                0.6: 0.095,
                0.7: 0.075,
                0.8: 0.055,
                0.9: 0.03,
            }
            _, self.zeta_value = min(
                zeta_extension.items(), key=lambda x: abs(area_factor - x[0])
            )

        else:
            raise TypeError(f"Cant process reduction type information {TypeError}")


@dataclass
class TPiece:
    """
    Represents a component of type TPiece with inherited class type of circled or rectangled.
    Additionally, a class with substantial data is inherited for further calculation.

    Args:
        connector_a (Union[ComponentCircled, ComponentRectangled]): The first connector \
            of the TPiece.
        connector_b (Union[ComponentCircled, ComponentRectangled]): The second connector \
            of the TPiece.
    """

    connector_a: Union[ComponentCircled, ComponentRectangled]
    connector_b: Union[ComponentCircled, ComponentRectangled]
    componenttype: ComponentType = ComponentType.TPIECE
    zeta_value: float = field(init=False)

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks for the object.
        """
        self.get_zeta_value()

    def __str__(self) -> str:
        """
        Returns a string representation of the AirComponent object.

        If the shape of connector_a is RECTANGLED, the string includes the following information:
        - connector_a
        - width b: [width of connector_a] [mm]
        - height b: [height of connector_a] [mm]
        - area b: [area of connector_a] [mm^2]
        - width c: [width of connector_b] [mm]
        - height c: [height of connector_b] [mm]
        - area c: [area of connector_b] [mm^2]
        - zeta value: [zeta_value] [-]
        - shape type: [componenttype]

        If the shape of connector_a is not RECTANGLED, the string includes the \
            following information:
        - connector_a
        - diameter b: [diameter of connector_a] [mm]
        - area b: [area of connector_a] [mm^2]
        - diameter c: [diameter of connector_b] [mm]
        - area c: [area of connector_b] [mm^2]
        - zeta value: [zeta_value] [-]
        - shape type: [componenttype]

        Returns:
        - A string representation of the AirComponent object.
        """
        if self.connector_a.shape is ComponentForm.RECTANGLED:
            msg = f"""{self.connector_a}
    width b: {self.connector_a.width:.0f} [mm], heigth b: {self.connector_a.heigth:.0f} [mm]
    area b: {self.connector_a.area:.2f} [mm^2]
    width c: {self.connector_b.width:.0f} [mm], heigth b: {self.connector_b.heigth:.0f} [mm]
    area c: {self.connector_b.area:.2f} [mm^2]
    zeta value: {self.zeta_value:.4f} [-]
    shape type: {self.componenttype}"""

        else:
            msg = f"""{self.connector_a}
    diameter b: {self.connector_a.diameter:.0f} [mm]
    area b: {self.connector_a.area:.2f} [mm^2]
    diameter c: {self.connector_b.diameter:.0f} [mm]
    area c: {self.connector_b.area:.2f} [mm^2]
    zeta value: {self.zeta_value:.4f} [-]
    shape type: {self.componenttype}"""

        return msg

    def _get_factor_v1_v(self) -> float:
        """Calculate a specific factor for further processing.

        This method calculates a factor by dividing the area of `connector_a` by the \
            sum of the areas of `connector_a` and `connector_b`.

        Returns:
            float: The calculated factor, which is dimensionless.
        """
        return self.connector_a.area / (self.connector_a.area + self.connector_b.area)

    def get_zeta_value(self) -> None:
        """calculate and set the zeta value

        This method calculates and sets the zeta value based on the factor_v1_v value.
        The zeta value is determined by finding the closest key-value pair in the \
            zeta_tpiece dictionary
        to the factor_v1_v value.
        """
        zeta_tpiece = {0.4: 6.3, 0.6: 2.8, 0.8: 1.6, 1.0: 1.0, 1.2: 0.8}
        factor_v1_v = self._get_factor_v1_v()
        _, self.zeta_value = min(
            zeta_tpiece.items(), key=lambda x: abs(factor_v1_v - x[0])
        )


@dataclass
class Flap:
    """
    Represents a flap air component.

    Attributes:
        connector (Union[ComponentCircled, ComponentRectangled]): The connector type of the flap.
        componenttype (ComponentType): The type of the air component.
        alpha_angle (float): The calculated alpha angle.

    Methods:
        __str__(): Returns a string representation of the Flap object.
        get_adjust_angle(volume_flow): Calculates the adjustment angle based on the \
            given volume flow rate.
        get_pressure_drop(alpha_angle): Calculates the pressure drop across the air component.
    """

    connector: Union[ComponentCircled, ComponentRectangled]
    componenttype: ComponentType = ComponentType.FLAP
    alpha_angle: float = field(init=False)

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks for the object.
        """
        self.alpha_angle = 0

    def __str__(self) -> str:
        """
        Returns a string representation of the Flap object.

        The string includes the connector, angle in degrees and radians, zeta value, and shape type.

        Returns:
            str: A string representation of the Flap object.
        """
        msg = f"""{self.connector}
    shape type: {self.componenttype}"""
        return msg

    def get_adjust_angle(self, volume_flow: float) -> float:
        """
        Calculates the adjustment angle based on the given volume flow rate.

        Args:
            volume_flow (float): The volume flow rate in m³/h.

        Returns:
            float: The angle in degrees.
        """
        # convert m³/h to m³/s
        volume_flow = volume_flow / 3600
        self.alpha_angle = -634.6 * volume_flow + 92.88
        return self.alpha_angle

    def get_pressure_drop(self, alpha_angle: float) -> float:
        """
        Calculates the pressure drop across the air component.

        Parameters:
        alpha_angle (float): The angle of attack in degrees.

        Returns:
        float: The pressure drop in units of Pascal.
        """
        return 1.112 * alpha_angle + 109.9


@dataclass
class Airterminal:
    """
    Represents an air terminal component.

    Attributes:
        connector (Union[ComponentCircled, ComponentRectangled]): The connector of the air terminal.
        componenttype (ComponentType): The type of the air terminal component.
    """

    connector: Union[ComponentCircled, ComponentRectangled]
    componenttype: ComponentType = ComponentType.AIRTERMINAL
    zeta_value: float = field(init=False)

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks for the object.
        """
        self.zeta_value = 0

    def __str__(self) -> str:
        """
        Returns a string representation of the Flap object.

        The string includes the connector, angle in degrees and radians, zeta value, and shape type.

        Returns:
            str: A string representation of the Flap object.
        """
        msg = f"""{self.connector}
    shape type: {self.componenttype}"""
        return msg


@dataclass
class ComponentList:
    """
    A list of all instanced components.

    Args:
        obj (List[Union[Duct, Bow, Reduction, TPiece]], optional): The list of components. \
            Defaults to an empty list.
    """

    obj: List[Union[Duct, Bow, Reduction, TPiece]] = field(init=False)

    def __post_init__(self) -> None:
        """
        This method is called after the object has been initialized.
        It initializes the 'obj' attribute as an empty list.
        """
        self.obj = []

    def __str__(self) -> str:
        """
        Returns a string representation of the object.

        Returns:
            str: The string representation of the object.
        """
        msg = ""
        for item in self.obj:
            if item.componenttype in (ComponentType.DUCT, ComponentType.BOW):
                msg = (
                    msg
                    + f"""-----------------------------------------------------------------------
ID: {item.connector_a.general.component_id}
Port A: {item.connector_a.general.port_a}, Port B: {item.connector_a.general.port_b}
shape form: {item.connector_a.shape}
shape type: {item.componenttype}\n"""
                )
            if item.componenttype in (ComponentType.TPIECE, ComponentType.REDUCTION):
                msg = (
                    msg
                    + f"""-----------------------------------------------------------------------
ID: {item.connector_a.general.component_id}
Port A: {item.connector_a.general.port_a}, Port B: {item.connector_a.general.port_b}
shape form: {item.connector_a.shape}
shape type: {item.componenttype}\n"""
                )
        return msg


# Main - Test Environment
if __name__ == "__main__":
    Component_List = ComponentList()
    Bow01 = ComponentGeneral(
        component_id=1,
        orientation=ComponentOrientation.VERTICAL,
        airtype=ComponentAirType.OA,
        port_a="a",
        port_b="b",
    )
    Bow02 = ComponentRectangled(Bow01, width=600, heigth=200)
    Bow10 = Bow(Bow02, angle=90)
    Component_List.obj.append(Bow10)
    Bow11 = ComponentGeneral(
        component_id=2,
        orientation=ComponentOrientation.VERTICAL,
        airtype=ComponentAirType.OA,
        port_a="b",
        port_b="c",
    )
    Bow12 = ComponentCircled(Bow11, diameter=100, length=4000)
    Bow20 = Bow(Bow12, angle=90)
    Component_List.obj.append(Bow20)
    Duct01 = ComponentGeneral(
        component_id=3,
        orientation=ComponentOrientation.HORIZONTAL,
        airtype=ComponentAirType.OA,
        port_a="c",
        port_b="d",
    )
    Duct02 = ComponentCircled(Duct01, diameter=200)
    Duct10 = Duct(Duct02, mean_velocity=1.5)
    Component_List.obj.append(Duct10)
    Tpiece01 = ComponentGeneral(
        component_id=4,
        orientation=ComponentOrientation.HORIZONTAL,
        airtype=ComponentAirType.OA,
        port_a="d",
        port_b="e",
    )
    Tpiece02 = ComponentCircled(Tpiece01, diameter=100)
    Tpiece03 = ComponentCircled(Tpiece01, diameter=100)
    Tpiece10 = TPiece(connector_a=Tpiece02, connector_b=Tpiece03)
    Component_List.obj.append(Tpiece10)
    Reduction01 = ComponentGeneral(
        component_id=5,
        orientation=ComponentOrientation.HORIZONTAL,
        airtype=ComponentAirType.OA,
        port_a="e",
        port_b="f",
    )
    Reduction02 = ComponentCircled(Reduction01, diameter=100)
    Reduction03 = ComponentCircled(Reduction01, diameter=200)
    Reduction04 = Reduction(
        connector_a=Reduction02,
        connector_b=Reduction03,
        reductiontype=ReductionType.EXTENSION,
    )
    Component_List.obj.append(Reduction04)
    Reduction10 = ComponentGeneral(
        component_id=6,
        orientation=ComponentOrientation.HORIZONTAL,
        airtype=ComponentAirType.OA,
        port_a="f",
        port_b="g",
    )
    Reduction11 = ComponentRectangled(Reduction10, width=600, heigth=200)
    Reduction12 = ComponentRectangled(Reduction10, width=300, heigth=200)
    Reduction13 = Reduction(
        connector_a=Reduction11,
        connector_b=Reduction12,
        reductiontype=ReductionType.NARROWING,
    )
    Component_List.obj.append(Reduction13)
    ic(Component_List)
    # Trying manipulating deep data
    # print(Component_List.obj[1])
    # print("----------------------------")
    # Component_List.obj[1].port_a_b.general.port_a = "DD"
    # print(Component_List)
    # print("----------------------------")
    # print(Bow20)
