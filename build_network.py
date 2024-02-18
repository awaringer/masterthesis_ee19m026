# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
The build_network module contains classes and functions for building a ventilation network based \
    on the imported data.

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
13-01-2024		AW	adding more flexibility with dicts
7-01-2024		AW	extend object AssignComponents
5-01-2024		AW	refactoring
3-01-2024		AW	creation


"""
# Futures
from __future__ import print_function

# Specific Imports
from enum import Enum, auto
from typing import List, Dict, Union
from dataclasses import dataclass, field

# from icecream import ic

# Libs
import pandas as pd
import numpy as np

# Own modules
from air_components import (
    ComponentCircled,
    ComponentForm,
    ComponentGeneral,
    ComponentList,
    ComponentOrientation,
    ComponentRectangled,
    ComponentType,
    Bow,
    Duct,
    Reduction,
    ComponentAirType,
    TPiece,
    ReductionType,
    Flap,
    Airterminal,
)
from building_information import Room
from thermodynamics import Pressure

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"build_network.py"


class DirectionType(Enum):
    """Definition Direction Type Flag"""

    LEFT = auto()
    RIGHT = auto()


class PostOrderMode(Enum):
    """Definition PostOrder Mode Flag"""

    ACTIVE = auto()
    DEMO = auto()


class Node:
    """nodes for mapping the ventilation system"""

    def __init__(
        self,
        nodeid=Union[Bow, Reduction, TPiece, Duct, Flap, Room],
        volume_flow: float = 0,
        pressure_drop: float = 0,
    ):
        self.nodeid = nodeid
        self.volume_flow = volume_flow
        self.pressure_drop = pressure_drop
        self.left = None
        self.right = None

    def add(self, direction: DirectionType, new_node):
        """adds nodes for a later point of time

        Args:
            direction (DirectionType): add left or right to the tree
            nodeid (str): id of the node

        Raises:
            ValueError: DirectionType not properly defined

        Returns:
            Node: new created node
        """
        # new_node = Node(nodeid)
        if direction == DirectionType.LEFT:
            self.left = new_node
        elif direction == DirectionType.RIGHT:
            self.right = new_node
        else:
            raise ValueError(
                "Invalid direction. Use 'DirectionType.LEFT' or 'DirectionType.RIGHT'."
            )
        return new_node

    def postorder_traversal(self) -> tuple[str, str]:
        """Performs a postorder traversal of the network tree.

        Returns:
            tuple[str, str]: A tuple containing the total volume flow and total pressure drop.

        Notes:
            This method traverses the network tree in a postorder manner, visiting the left child,
            then the right child, and finally the current node. It calculates the total volume flow
            and total pressure drop of the network based on the connector mapping provided.

        Raises:
            None.
        """
        # return node or None
        left_result = self.left.postorder_traversal() if self.left else (0, 0)
        right_result = self.right.postorder_traversal() if self.right else (0, 0)
        # right_result = self.right.postorder_traversal() if self.right else (0, 0)

        # if hasattr(self.nodeid, "connector"):
        #     obj_connector = self.nodeid.connector
        # elif hasattr(self.nodeid, "connector_a"):
        #     obj_connector = self.nodeid.connector_a
        # else:
        #     raise ValueError("Connector can't be found")

        if self.nodeid.componenttype == ComponentType.ROOM:
            volume_flow = self.nodeid.volume_flow
            return (volume_flow, 0)

        # left and right results separated
        left_volume_flow, left_pressure_drop = left_result
        right_volume_flow, right_pressure_drop = right_result

        # sum up volume flows
        if self.nodeid.componenttype == ComponentType.TPIECE:
            total_volume_flow = left_volume_flow + right_volume_flow
            self.volume_flow = total_volume_flow
        elif self.nodeid.componenttype == ComponentType.AIRTERMINAL:
            total_volume_flow = self.volume_flow
        else:
            total_volume_flow = left_volume_flow
            self.volume_flow = total_volume_flow

        if self.pressure_drop == 0:
            # sum up pressure drops
            if self.nodeid.componenttype == ComponentType.FLAP:
                angle = self.nodeid.get_adjust_angle(total_volume_flow)
                self.pressure_drop = self.nodeid.get_pressure_drop(alpha_angle=angle)
            # elif self.nodeid.componenttype == ComponentType.AIRTERMINAL:
            #     self.pressure_drop = self.pressure_drop
            else:
                self.pressure_drop = Pressure(
                    component=self.nodeid, volume_flow=self.volume_flow
                ).pressure_drop

        total_pressure_drop = (
            self.pressure_drop + left_pressure_drop + right_pressure_drop
        )

        # ic(obj_connector.general.component_id, self.pressure_drop)
        # ic(
        #     obj_connector.general.component_id,
        #     self.nodeid.componenttype,
        #     total_volume_flow,
        #     total_pressure_drop,
        # )

        return total_volume_flow, total_pressure_drop


class AssignComponents:
    """assignment of the components to the corresponding objects

    Args:
        components (pd.DataFrame): listing of total network components
        network (pd.DataFrame): the total network information
        component_type (Dict[str, Union[ComponentType, ComponentForm]]): defined types as enum
        shape_type (Dict[str, Union[ComponentType, ComponentForm]]): translation dict to \
                                                                     enum components
        df_assignments (Dict[str, str]): name assignments

    Returns:
        self.component_list (ComponentList): a total list of all components

    """

    def __init__(
        self,
        components: pd.DataFrame,
        network: pd.DataFrame,
        component_type: Dict[str, Union[ComponentType, ComponentForm]],
        df_assignments: Dict[str, str],
    ) -> None:
        """
        Initializes the BuildNetwork class.

        Args:
            components (pd.DataFrame): DataFrame containing component information.
            network (pd.DataFrame): DataFrame containing network information.
            component_type (Dict[str, Union[ComponentType, ComponentForm]]): Dictionary \
                mapping component names to their types.
            df_assignments (Dict[str, str]): Dictionary mapping column names to their \
                corresponding assignments.

        Returns:
            None
        """
        self.component_list = ComponentList()
        for _, row in components.iterrows():
            componenttype = component_type.get(row[df_assignments.get("component")])
            airtype = component_type.get(row[df_assignments.get("system")])

            component = self.assign_components(
                row=row,
                network=network,
                componenttype=componenttype,
                airtype=airtype,
                shape_type=component_type,
                df_assignments=df_assignments,
            )
            self.component_list.obj.append(component)

    def assign_components(
        self,
        row: pd.Series,
        network: pd.DataFrame,
        componenttype: ComponentType,
        airtype: ComponentAirType,
        shape_type: Dict[str, Union[ComponentType, ComponentForm]],
        df_assignments: Dict[str, str],
    ) -> Union[Duct, Bow, TPiece, Reduction]:
        """merges the classes for the completion of the components

        Args:
            row (pd.Series): raw data for the component
            network (pd.DataFrame): the total network information
            componenttype (ComponentType): the defined component type as enum
            shape_type (Dict[str, Union[ComponentType, ComponentForm]]): translation dict to \
                                                                         enum components
            df_assignments (Dict[str, str]): name assignments

        Returns:
            Union[Duct, Bow, TPiece, Reduction]: a defined and filled component
        """
        general_information = self.assign_component_general(
            row=row,
            network=network,
            componenttype=componenttype,
            airtype=airtype,
            df_assignments=df_assignments,
        )

        form = self.assign_component_form(
            general=general_information,
            row=row,
            shape_type=shape_type,
            df_assignments=df_assignments,
        )

        # conditions for proper creation
        if componenttype == ComponentType.DUCT:
            component = self.assign_duct(form)

        elif componenttype == ComponentType.BOW:
            component = self.assign_bow(
                connector=form, row=row, df_assignments=df_assignments
            )

        elif componenttype == ComponentType.TPIECE:
            form1 = self.assign_component_form(
                general=general_information[0],
                row=row,
                shape_type=shape_type,
                df_assignments=df_assignments,
            )
            form2 = self.assign_component_form(
                general=general_information[1],
                row=row,
                shape_type=shape_type,
                df_assignments=df_assignments,
            )
            component = self.assign_tpiece(connector_a=form1, connector_b=form2)

        elif componenttype == ComponentType.REDUCTION:
            component = self.assign_reduction(connector_a=form[0], connector_b=form[1])

        elif componenttype == ComponentType.ROOM:
            component = self.assign_room(connector=form)

        elif componenttype == ComponentType.FLAP:
            component = self.assign_flap(connector=form)

        elif componenttype == ComponentType.AIRTERMINAL:
            component = self.assign_airterminal(connector=form)

        else:
            component = None

        return component

    def assign_component_general(
        self,
        row: pd.Series,
        network: pd.DataFrame,
        componenttype: ComponentType,
        airtype: ComponentAirType,
        df_assignments: Dict[str, str],
    ) -> ComponentGeneral:
        """Merging the information to create the top level obj

        Args:
            row (pd.Series): raw data for the component
            network (pd.DataFrame): the total network information
            componenttype (ComponentType): the defined component type as enum
            df_assignments (Dict[str, str]): name assignments

        Raises:
            ValueError: ports can't be defined properly

        Returns:
            ComponentGeneral: top level obj for creating components
        """
        parent_child_assigment = [
            df_assignments.get("child"),
            df_assignments.get("parent"),
        ]
        seq_parent_child = {
            "ZUL": [parent_child_assigment[0], parent_child_assigment[1]],
            "ABL": [parent_child_assigment[1], parent_child_assigment[0]],
            "FOL": [parent_child_assigment[0], parent_child_assigment[1]],
            "AUL": [parent_child_assigment[0], parent_child_assigment[1]],
            "ROOM": [parent_child_assigment[0], parent_child_assigment[1]],
        }

        air_system = row[df_assignments.get("system")]
        component_id = row[df_assignments.get("nodeid")]
        orientation = ComponentOrientation.HORIZONTAL

        # define port_a and port_b and optional port_c for later component assigment
        try:
            if componenttype == ComponentType.AIRTERMINAL:
                port_a = (
                    network[
                        network[seq_parent_child.get(air_system)[0]] == component_id
                    ][seq_parent_child.get(air_system)[1]]
                    .astype(str)
                    .item()
                )
                port_b = ""

            elif componenttype == ComponentType.TPIECE:
                port_a = (
                    network[
                        network[seq_parent_child.get(air_system)[0]] == component_id
                    ][seq_parent_child.get(air_system)[1]]
                    .astype(str)
                    .item()
                )
                port_b_c = (
                    network[
                        network[seq_parent_child.get(air_system)[1]] == component_id
                    ][seq_parent_child.get(air_system)[0]]
                    .astype(str)
                    .values
                )
                port_b = port_b_c[0]
                port_c = port_b_c[1]

                connector_a = ComponentGeneral(
                    component_id=str(component_id),
                    orientation=orientation,
                    airtype=airtype,
                    port_a=port_a,
                    port_b=port_b,
                )
                connector_b = ComponentGeneral(
                    component_id=str(component_id),
                    orientation=orientation,
                    airtype=airtype,
                    port_a=port_a,
                    port_b=port_c,
                )
                return connector_a, connector_b

            elif componenttype == ComponentType.ROOM:
                port_b = None
                port_a = (
                    network[
                        network[seq_parent_child.get(air_system)[0]] == component_id
                    ][seq_parent_child.get(air_system)[1]]
                    .astype(str)
                    .item()
                )

            elif row["component"] == "FAN":
                # TODO: FAN
                return None

            elif air_system == "ROOT":
                return None

            else:
                port_a = (
                    network[
                        network[seq_parent_child.get(air_system)[0]] == component_id
                    ][seq_parent_child.get(air_system)[1]]
                    .astype(str)
                    .item()
                )
                port_b = (
                    network[
                        network[seq_parent_child.get(air_system)[1]] == component_id
                    ][seq_parent_child.get(air_system)[0]]
                    .astype(str)
                    .item()
                )

        except ValueError as exc:
            raise ValueError(
                f" NodeId: {component_id}, Form: {row.component}, Error: {exc}"
            ) from exc

        return ComponentGeneral(
            component_id=str(component_id),
            orientation=orientation,
            airtype=airtype,
            port_a=port_a,
            port_b=port_b,
        )

    def assign_component_form(
        self,
        general: ComponentGeneral,
        row: pd.Series,
        shape_type: Dict[str, Union[ComponentType, ComponentForm]],
        df_assignments: Dict[str, str],
    ) -> Union[ComponentCircled, ComponentRectangled]:
        """Merging the information to create the second level obj

        Args:
            general (ComponentGeneral): top level obj (mandatory)
            row (pd.Series): raw data for the component
            shape_type (Dict[str, Union[ComponentType, ComponentForm]]): translation dict to \
                                                                         enum components
            df_assignments (Dict[str, str]): name assignments

        Returns:
            Union[ComponentCircled, ComponentRectangled]: either a round or square connection
        """
        shape = shape_type.get(row[df_assignments.get("form")])
        length = float(row[df_assignments.get("length")])

        if shape == ComponentForm.CIRCLED:
            diameter = int(float(row[df_assignments.get("dimension")]))
            return ComponentCircled(general=general, diameter=diameter, length=length)

        if shape == ComponentForm.RECTANGLED:
            width_heigth = row[df_assignments.get("dimension")].split("x")
            width = int(float(width_heigth[0]))
            heigth = int(float(width_heigth[1]))
            return ComponentRectangled(
                general=general, width=width, heigth=heigth, length=length
            )

        if shape == ComponentType.REDUCTION:
            dimensions = row[df_assignments.get("dimension")].split("-")
            if len(dimensions) == 2:
                diameter_a = int(float(dimensions[0]))
                diameter_b = int(float(dimensions[1]))
                port_a = ComponentCircled(
                    general=general, length=length, diameter=diameter_a
                )
                port_b = ComponentCircled(
                    general=general, length=length, diameter=diameter_b
                )
            elif len(dimensions) == 3:
                diameter_a = int(float(dimensions[0]))
                width_b = int(float(dimensions[1]))
                heigth_b = int(float(dimensions[2]))
                port_a = ComponentCircled(
                    general=general, length=length, diameter=diameter_a
                )
                port_b = ComponentRectangled(
                    general=general, width=width_b, heigth=heigth_b, length=length
                )
            elif len(dimensions) == 4:
                width_a = int(float(dimensions[0]))
                heigth_a = int(float(dimensions[1]))
                width_b = int(float(dimensions[2]))
                heigth_b = int(float(dimensions[3]))
                port_a = ComponentRectangled(
                    general=general, width=width_a, heigth=heigth_a, length=length
                )
                port_b = ComponentRectangled(
                    general=general, width=width_b, heigth=heigth_b, length=length
                )
            else:
                raise ValueError(
                    f"Connectors for Reduction can't handled properly for: \
                        {row[df_assignments.get('nodeid')]}"
                )

            return port_a, port_b

        if shape == ComponentType.ROOM:
            room_dimensions = row[df_assignments.get("dimension")].split("x")
            room_dimensions.append(row.length)
            room_dimensions = [float(x) for x in room_dimensions]

            dict_keys = ["length", "height", "width"]
            room_dimensions = dict(zip(dict_keys, room_dimensions))
            return ComponentRectangled(
                general=general,
                width=room_dimensions["width"],
                heigth=room_dimensions["height"],
                length=room_dimensions["length"],
            )

    def assign_duct(
        self,
        connector: Union[ComponentCircled, ComponentRectangled],
    ) -> Duct:
        """composition of a pipe object

        Args:
            connector (Union[ComponentCircled, ComponentRectangled]): dimension of the obj

        Returns:
            Duct: object
        """
        component = Duct(connector=connector)
        return component

    def assign_bow(
        self,
        connector: Union[ComponentCircled, ComponentRectangled],
        row: pd.Series,
        df_assignments: Dict[str, str],
    ) -> Bow:
        """composition of a bow object

        Args:
            connector (Union[ComponentCircled, ComponentRectangled]): dimension of the obj
            row (pd.Series): raw data for the component
            df_assignments (Dict[str, str]): name assignments

        Returns:
            Bow: object
        """
        angle = int(float(row[df_assignments.get("angle")]))
        component = Bow(connector=connector, angle=angle)
        return component

    def assign_tpiece(
        self,
        connector_a: Union[ComponentCircled, ComponentRectangled],
        connector_b: Union[ComponentCircled, ComponentRectangled],
    ) -> TPiece:
        """composition of a T-piece object

        Args:
            connector_a (Union[ComponentCircled, ComponentRectangled]): dimension of port_a_b
            connector_b (Union[ComponentCircled, ComponentRectangled]): dimension of port_a_c

        Returns:
            TPiece: object
        """
        component = TPiece(connector_a=connector_a, connector_b=connector_b)
        return component

    def assign_reduction(
        self,
        connector_a: Union[ComponentCircled, ComponentRectangled],
        connector_b: Union[ComponentCircled, ComponentRectangled],
    ) -> Reduction:
        """composition of a reduction object

        Args:
            port_a (Union[ComponentCircled, ComponentRectangled]): dimension of port_a_b
            port_b (Union[ComponentCircled, ComponentRectangled]): dimension of port_a_c

        Returns:
            Reduction: object
        """
        if connector_a.area > connector_b.area:
            reduction_type = ReductionType.NARROWING
        else:
            reduction_type = ReductionType.EXTENSION
        component = Reduction(
            connector_a=connector_a,
            connector_b=connector_b,
            reductiontype=reduction_type,
        )
        return component

    def assign_room(self, connector: ComponentRectangled) -> Room:
        """
        Assigns a room to a given connector.

        Args:
            connector (ComponentRectangled): The connector to assign a room to.

        Returns:
            Room: The assigned room.

        """
        connector.area = connector.length * connector.width / 1_000_000
        room_id = "Room" + "_" + str(connector.general.component_id)
        component = Room(
            room_number=room_id,
            connector=connector,
            persons=1,
            area=connector.area,
            height=connector.heigth / 1_000,
        )
        return component

    def assign_flap(
        self, connector: Union[ComponentCircled, ComponentRectangled]
    ) -> Flap:
        """
        Assigns a flap to a given connector.

        Args:
            connector (Union[ComponentCircled, ComponentRectangled]): The connector to assign a \
                flap to.

        Returns:
            Flap: The assigned flap.

        """
        component = Flap(connector=connector)
        return component

    def assign_airterminal(
        self,
        connector: Union[ComponentCircled, ComponentRectangled],
    ) -> Airterminal:
        """composition of a pipe object

        Args:
            connector (Union[ComponentCircled, ComponentRectangled]): dimension of the obj

        Returns:
            Duct: object
        """
        component = Airterminal(connector=connector)
        return component


@dataclass
class MergeNetwork:
    """merge dataframes to add information to parent and child

    Args:
        source (pd.DataFrame): component list
        target (pd.DataFrame): network list
        source_key (str): id source_data for comparing columns
        target_keys (tuple): id target_data for comparing columns

    Returns:
        data (pd.DataFrame): modified target_data
    """

    source: pd.DataFrame
    target: pd.DataFrame
    source_key: str = field(default="nodeid")
    target_keys: tuple = field(default_factory=tuple)
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.set_default()
        df_parent = self.merge_dataframes(
            source_data=self.source,
            target_data=self.target,
            src_key=self.source_key,
            tgt_key=self.target_keys[0],
        )
        self.data = self.merge_dataframes(
            source_data=self.source,
            target_data=df_parent,
            src_key=self.source_key,
            tgt_key=self.target_keys[1],
        )

    def set_default(self) -> None:
        """store default values"""
        if not self.target_keys:
            self.target_keys = ["parent", "child"]

    def merge_dataframes(
        self,
        source_data: pd.DataFrame,
        target_data: pd.DataFrame,
        src_key: str,
        tgt_key: str,
    ) -> pd.DataFrame:
        """merge dataframes to add information to parent and child

        Args:
            source_data (pd.DataFrame): component list
            target_data (pd.DataFrame): network list
            src_key (str): id source_data for comparing columns
            tgt_key (str): id target_data for comparing columns

        Returns:
            pd.DataFrame: modified target_data
        """
        sfx = "_" + tgt_key
        source_data = source_data.add_suffix(sfx)
        src_key = src_key + sfx
        merge_data = pd.merge(
            left=source_data,
            right=target_data,
            left_on=src_key,
            right_on=tgt_key,
        )

        return merge_data


def assign_child_nodes(node_dict: Dict[str, Node]) -> Dict[str, Node]:
    """
    Assigns child nodes to each node in the node dictionary based on the connector mapping.

    Args:
        node_dict (Dict[str, Node]): A dictionary containing nodes, where the key is the node \
            ID and the value is the Node object.

    Returns:
        Dict[str, Node]: A dictionary containing nodes with assigned child nodes.
    """

    for _, node in node_dict.items():
        if hasattr(node.nodeid, "connector"):
            left_node = node.nodeid.connector.general.port_b
        elif hasattr(node.nodeid, "connector_a"):
            left_node = node.nodeid.connector_a.general.port_b
        else:
            raise ValueError("Connector can't be found")

        if node.nodeid.componenttype == ComponentType.TPIECE:
            right_node = node.nodeid.connector_b.general.port_b
            child_node2 = node_dict.get(right_node)
            node.add(DirectionType.RIGHT, child_node2)

        child_node = node_dict.get(left_node)
        node.add(DirectionType.LEFT, child_node)
    return node_dict


def create_nodes(
    comp_list: Dict[str, Union[Bow, Reduction, TPiece, Duct, Flap]],
    node_ids: list,
):
    """based on imports instance new nodes

    Args:
        comp_list Dict[str, Union[Bow, Reduction, TPiece, Duct]: list of components
        node_ids (list): list of node ids

    Returns:
        node_dict (dict): listing of all Nodes
    """
    node_dict = {}

    # building nodes
    for nodeid in node_ids:
        new_node = Node(nodeid=comp_list.get(nodeid))
        node_dict[nodeid] = new_node

    node_dict = assign_child_nodes(node_dict=node_dict)

    return node_dict


def search_node(
    comp_list: ComponentList,
    search_value: str,
) -> Union[Bow, Reduction, TPiece, Duct]:
    """identify the correct node depeneding on the nodeid \
    only for air_components!

    Args:
        comp_list (ComponentList): list of specific components
        search_value (str): nodeid to find proper object
        connectors (dict): sub classes definition

    Raises:
        ValueError: component cant be found

    Returns:
        Union[Bow, Reduction, TPiece, Duct]: node depending on nodeid parameter
    """
    for obj in comp_list:
        if hasattr(obj, "connector"):
            if search_value == obj.connector.general.component_id:
                return obj
        if hasattr(obj, "connector_a"):
            if search_value == obj.connector_a.general.component_id:
                return obj
    raise ValueError("Component can't be found")


def get_start_roots(
    components: pd.DataFrame,
    network: pd.DataFrame,
    df_assignments: Dict[str, str],
    ahu_definition: str = "AIRHANDLER",
) -> dict:
    """identify the starting points for building the network

    Args:
        components (pd.DataFrame): listing of total network components
        network (pd.DataFrame): the total network information
        df_assignments (Dict[str, str]): name assignments
        ahu_definition (str, optional): name of search string from import. Defaults to "AIRHANDLER".

    Returns:
        dict: start points ordered by flow type
    """
    ahu_id = components[
        components[df_assignments.get("component")] == ahu_definition
    ].nodeid.values.item()
    abl = str(network[network[df_assignments.get("child")] == ahu_id].parent.item())
    temp = network[network[df_assignments.get("parent")] == ahu_id].child.values

    start_roots = {"ABL": abl}
    for value in temp:
        start_roots[
            components[components[df_assignments.get("nodeid")] == value].system.item()
        ] = str(value)

    return start_roots


def component_list_to_dict(
    comp_list: List[Union[Duct, TPiece, Bow, Reduction]],
) -> Dict[str, Union[Duct, TPiece, Bow, Reduction]]:
    """convert the component list to a dict

    Args:
        comp_list (List[Union[Duct, TPiece, Bow, Reduction]]): list of all instanced components
        connector_dict (dict): sub classes definition

    Raises:
        ValueError: _description_

    Returns:
        Dict[str, Union[Duct, TPiece, Bow, Reduction]]: dict assignment nodeid -> component
    """
    component_dict = {}

    for component in comp_list:
        if hasattr(component, "connector"):
            nodeid = component.connector.general.component_id
        elif hasattr(component, "connector_a"):
            nodeid = component.connector_a.general.component_id
        else:
            raise ValueError("Connector can't be found")

        component_dict[nodeid] = component

    return component_dict


def random_demo() -> dict:
    """
    Generates a dictionary of random demo results.

    Returns:
        dict: A dictionary containing the random demo results.
    """
    results_lit = {}
    base_lit = {
        "1": 4,
        "2": 11.7,
        "6": 5.3,
        "8": 5.1,
        "9": 0,
        "10": 1.7,
        "11": 3.7,
        "19": 4.1,
        "20": 4.3,
        "27": 0.45,
        "28": 0.9,
        "29": 2.9,
        "21": 6.6,
        "26": 1.16,
        "23": 1.4,
        "22": 1.3,
        "25": 0,
    }
    sections = {
        "1": ["3", "5"],
        "10": ["12", "14", "16", "18"],
        "2": ["4"],
        "11": ["13", "15", "17"],
        "21": ["31"],
        "25": ["33", "37", "40"],
        "26": ["24", "32", "36", "39"],
        "22": ["30", "34"],
        "23": ["35"],
        "29": ["38"],
    }

    rand_range = [0.95, 1.03]
    for key, value in base_lit.items():
        results_lit[key] = round(
            value * np.random.uniform(rand_range[0], rand_range[1]), 2
        )

        if sections.get(key) is not None:
            for add_keys in sections.get(key):
                results_lit[add_keys] = results_lit[key]

    sorted_dict = {key: results_lit[key] for key in sorted(results_lit)}
    return sorted_dict


def create_pd_dataframe(data) -> pd.DataFrame:
    """
    Creates a pandas dataframe from the given data.

    Args:
        data (list): A list containing the data.

    Returns:
        pd.DataFrame: A pandas dataframe containing the data.
    """
    return pd.DataFrame(data)


def create_pd_series(data, description) -> pd.Series:
    """
    Creates a pandas series from the given data.

    Args:
        data (list): A list containing the data.

    Returns:
        pd.Series: A pandas series containing the data.
    """
    if len(data) == 5:
        idx = [
            "Teilstrecke 1",
            "Teilstrecke 2",
            "Teilstrecke 3",
            "Teilstrecke 4",
            "Teilstrecke 5",
        ]
    else:
        idx = [
            "Teilstrecke 1",
            "Teilstrecke 1+4",
            "Teilstrecke 1+4+5",
        ]

    return pd.Series(
        data,
        index=idx,
        name=description,
    )


# Main - Test Environment
if __name__ == "__main__":
    pass
