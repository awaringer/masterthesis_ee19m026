# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
main module for the masterthesis

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------


"""
# Futures
from __future__ import print_function

# Built-in/Generic Imports
import warnings

# Specific Imports
from timeit import default_timer as timer
from typing import Dict
from icecream import ic

# Libs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Own modules
from import_data import (
    ImportData,
    DocumentType,
    ImportType,
)
from build_network import (
    PostOrderMode,
    component_list_to_dict,
    create_nodes,
    create_pd_dataframe,
    create_pd_series,
    Node,
    MergeNetwork,
    AssignComponents,
)

# from pmv_ppd import PMV_PPD
from air_components import (
    ComponentForm,
    ComponentType,
    ComponentAirType,
)

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"main.py"


def main():
    """
    This is the main function of the program.
    It imports information, builds a component network, calculates partial routes,
    compares routes, and prints the results.
    """
    comps, cons = import_information()
    ra_nodes = build_component_network(comps, cons)

    # calculate the pressure drops for the calculated and literature routes
    calculated_routes = calculate_partial_routes(ra_nodes)
    calculated_routes = list(calculated_routes)
    series_calculated = create_pd_series(calculated_routes, description="berechnet")
    ic(calculated_routes)
    literature_routes = get_literature_routes()
    literature_routes = list(literature_routes)
    series_literature = create_pd_series(literature_routes, description="Literatur")
    ic(literature_routes)
    df_compare_routes = create_pd_dataframe([series_calculated, series_literature])
    df_compare_routes.to_excel(
        "D:\\GitHub\\masterthesis\\masterthesis\\export\\routes.xlsx"
    )
    # sum up the pressure drops for the calculated and literature routes
    calculated_routes_line = []
    calculated_routes_line.append(calculated_routes[0])
    calculated_routes_line.append((calculated_routes[0] + calculated_routes[3]))
    calculated_routes_line.append(
        (calculated_routes[0] + calculated_routes[3] + calculated_routes[4])
    )
    series_calculated_line = create_pd_series(
        calculated_routes_line, description="berechnet"
    )
    literature_routes_line = []
    literature_routes_line.append(literature_routes[0])
    literature_routes_line.append((literature_routes[0] + literature_routes[3]))
    literature_routes_line.append(
        (literature_routes[0] + literature_routes[3] + literature_routes[4])
    )
    series_literature_line = create_pd_series(
        literature_routes_line, description="Literatur"
    )
    df_compare_total_routes = create_pd_dataframe(
        [series_calculated_line, series_literature_line]
    )
    df_compare_total_routes.to_excel(
        "D:\\GitHub\\masterthesis\\masterthesis\\export\\total_routes.xlsx"
    )

    # plot the comparison of the calculated and literature routes
    plot_bar_comparison_ger(calculated_routes, literature_routes)
    plot_line_comparision_ger(calculated_routes_line, literature_routes_line)


def plot_line_comparision_ger(calculated_routes, literature_routes):
    """
    Plots a line comparison of the calculated and literature routes.

    Args:
        calculated_routes (list): A list containing the calculated routes.
        literature_routes (list): A list containing the literature routes.
    """

    plt.style.use("fivethirtyeight")
    labels = [
        "Teilstrecke 1",
        "Teilstrecke 1+4",
        "Teilstrecke 1+4+5",
    ]
    x = np.arange(len(labels))

    fig, ax = plt.subplots()
    ax.plot(x, calculated_routes, label="berechnet")
    ax.plot(x, literature_routes, label="Literatur")

    ax.set_xlabel("Teilstrecken")
    ax.set_ylabel("Druckabfall [Pa]")
    ax.set_title("Druckabfallsvergleich Rohrkanalsystem")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.show()


def plot_bar_comparison_ger(calculated_routes, literature_routes):
    """
    Plots a bar comparison of the calculated and literature routes.

    Args:
        calculated_routes (list): A list containing the calculated routes.
        literature_routes (list): A list containing the literature routes.
    """

    plt.style.use("fivethirtyeight")
    labels = [
        "Teilstrecke 1",
        "Teilstrecke 2",
        "Teilstrecke 3",
        "Teilstrecke 4",
        "Teilstrecke 5",
    ]
    x = np.arange(len(labels))

    fig, ax = plt.subplots()
    bar_width = 0.4
    opacity = 0.8

    rects1 = ax.bar(
        x - bar_width / 2,
        calculated_routes,
        bar_width,
        alpha=opacity,
        color="b",
        label="berechnet",
    )
    rects2 = ax.bar(
        x + bar_width / 2,
        literature_routes,
        bar_width,
        alpha=opacity,
        color="g",
        label="Literatur",
    )

    for rect in rects1 + rects2:
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2.0,
            1.01 * height,
            "%.2f" % float(height),
            ha="center",
            va="bottom",
        )

    ax.set_xlabel("Teilstrecken")
    ax.set_ylabel("Druckabfall pro Teilstrecke [Pa]")
    ax.set_title("Druckabfallsvergleich pro Teilstrecke")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.show()


def plot_bar_comparison_eng(calculated_routes, literature_routes):
    """
    Plots a bar comparison of the calculated and literature routes.

    Args:
        calculated_routes (list): A list containing the calculated routes.
        literature_routes (list): A list containing the literature routes.
    """

    plt.style.use("fivethirtyeight")
    labels = ["Route 1", "Route 2", "Route 3", "Route 4", "Route 5"]
    x = np.arange(len(labels))

    fig, ax = plt.subplots()
    bar_width = 0.4
    opacity = 0.8

    rects1 = ax.bar(
        x - bar_width / 2,
        calculated_routes,
        bar_width,
        alpha=opacity,
        color="b",
        label="Calculated",
    )
    rects2 = ax.bar(
        x + bar_width / 2,
        literature_routes,
        bar_width,
        alpha=opacity,
        color="g",
        label="Literature",
    )

    for rect in rects1 + rects2:
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2.0,
            1.01 * height,
            "%.2f" % float(height),
            ha="center",
            va="bottom",
        )

    ax.set_xlabel("Routes")
    ax.set_ylabel("Pressure Drop [Pa]")
    ax.set_title("Pressure Drop Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.show()


def get_literature_routes() -> tuple:
    """
    Returns the pressure drop values for different routes in the literature.

    Returns:
        tuple: A tuple containing the pressure drop values for different routes.
    """
    pressure_drop_route1 = 15.1
    pressure_drop_route2 = 11.5
    pressure_drop_route3 = 22.4
    pressure_drop_route4 = 30.2
    pressure_drop_route5 = 67.5
    return (
        pressure_drop_route1,
        pressure_drop_route2,
        pressure_drop_route3,
        pressure_drop_route4,
        pressure_drop_route5,
    )


def calculate_partial_routes(ra_nodes) -> tuple:
    """
    Calculates the pressure drops for different partial routes in the network.

    Args:
        ra_nodes (dict): A dictionary containing the nodes in the network.

    Returns:
        tuple: A tuple containing the pressure drops for different partial routes.
    """
    # set volume flows
    ra_nodes.get("25").volume_flow = 240
    ra_nodes.get("33").volume_flow = 240
    ra_nodes.get("37").volume_flow = 240
    ra_nodes.get("39").volume_flow = 240

    # calculate route 1
    _, pressure_drop_ts1_1 = ra_nodes.get("31").postorder_traversal()
    _, pressure_drop_ts1_2 = ra_nodes.get("32").postorder_traversal()
    pressure_drop_ts1 = round(pressure_drop_ts1_1 - pressure_drop_ts1_2, 2)

    # calculate route 2
    _, pressure_drop_ts2_1 = ra_nodes.get("31").postorder_traversal()
    _, pressure_drop_ts2_2 = ra_nodes.get("34").postorder_traversal()
    pressure_drop_ts2 = round(pressure_drop_ts2_1 - pressure_drop_ts2_2, 2)

    # calculate route 3
    _, pressure_drop_ts3_1 = ra_nodes.get("19").postorder_traversal()
    _, pressure_drop_ts3_2 = ra_nodes.get("31").postorder_traversal()
    _, pressure_drop_ts3_3 = ra_nodes.get("20").postorder_traversal()
    pressure_drop_ts3 = round(
        pressure_drop_ts3_1 - pressure_drop_ts3_2 - pressure_drop_ts3_3, 2
    )

    # calculate route 4
    _, pressure_drop_ts4_1 = ra_nodes.get("19").postorder_traversal()
    _, pressure_drop_ts4_2 = ra_nodes.get("27").postorder_traversal()
    _, pressure_drop_ts4_3 = ra_nodes.get("21").postorder_traversal()
    pressure_drop_ts4 = round(
        pressure_drop_ts4_1 - pressure_drop_ts4_2 - pressure_drop_ts4_3, 2
    )

    # calculate route 5
    _, pressure_drop_ts5_1 = ra_nodes.get("8").postorder_traversal()
    _, pressure_drop_ts5_2 = ra_nodes.get("19").postorder_traversal()
    pressure_drop_ts5 = round(pressure_drop_ts5_1 - pressure_drop_ts5_2, 2)
    # ic(pressure_drop_ts5)
    return (
        pressure_drop_ts1,
        pressure_drop_ts2,
        pressure_drop_ts3,
        pressure_drop_ts4,
        pressure_drop_ts5,
    )


def build_component_network(comps, cons) -> Dict[str, Node]:
    """
    Builds a component network based on the given components and connections.

    Args:
        comps: DataFrame containing the component data.
        cons: DataFrame containing the connection data.

    Returns:
        A dictionary of nodes representing the component network.

    """
    component_assignment = {
        "ELBOW": ComponentType.BOW,
        "DUCTROUND": ComponentType.DUCT,
        "BRANCHDUCT": ComponentType.TPIECE,
        "CONFUSDIFFUS": ComponentType.REDUCTION,
        "DUCTANGULAR": ComponentType.DUCT,
        "AIRTERMINAL": ComponentType.AIRTERMINAL,
        "rectangled": ComponentForm.RECTANGLED,
        "circled": ComponentForm.CIRCLED,
        "reduction": ComponentType.REDUCTION,
        "ZUL": ComponentAirType.SA,
        "ABL": ComponentAirType.RA,
        "FOL": ComponentAirType.EA,
        "AUL": ComponentAirType.OA,
        "room": ComponentType.ROOM,
        "ROOM": ComponentType.ROOM,
        "FLAP": ComponentType.FLAP,
    }
    misc_assignment = {
        "child": "nodeid_child",
        "parent": "nodeid_parent",
        "component": "component",
        "system": "system",
        "nodeid": "nodeid",
        "form": "form",
        "length": "length",
        "dimension": "dimension",
        "angle": "angle",
    }
    component_list = AssignComponents(
        components=comps,
        network=cons,
        component_type=component_assignment,
        df_assignments=misc_assignment,
    ).component_list.obj

    filtered_comp_list = [value for value in component_list if value is not None]
    comp_list = component_list_to_dict(
        comp_list=filtered_comp_list,
    )

    test_system = "ZUL"
    filtered_values = (
        comps.loc[
            ((comps["system"] == test_system) | (comps["system"] == "ROOM")), "nodeid"
        ]
        .values.astype(str)
        .tolist()
    )
    ra_nodes = create_nodes(
        node_ids=filtered_values,
        comp_list=comp_list,
    )

    return ra_nodes


def import_information() -> pd.DataFrame:
    """
    Method for importing data.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing the imported components \
            and connections dataframes.
    """
    # import components and networks
    import_components = ImportData(
        # dirpath="/home/alex/codes/masterthesis/import",
        dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
        filename="Vertices.csv",
        document_type=DocumentType.CSV,
        import_flag=ImportType.COMPONENTS,
    ).data

    import_connections = ImportData(
        # dirpath="/home/alex/codes/masterthesis/import",
        dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
        filename="Edges.csv",
        document_type=DocumentType.CSV,
        import_flag=ImportType.NETWORK,
    ).data

    connections = MergeNetwork(
        source=import_components,
        target=import_connections,
        source_key="nodeid",
        target_keys=("parent", "child"),
    ).data

    return import_components, connections


if __name__ == "__main__":
    warnings.simplefilter(action="ignore", category=Warning)
    start = timer()
    main()
    end = timer()
    ic(f"The execution time is {end - start}s")
