# -*- coding: utf-8 -*-
"""
* DESCRIPTION:
This module can be used to import weather, profile and ventilation network data. 
for the time being, data is imported via xlsx or csv. in future, tm2 and tm3 
data can also be integrated.

In addition, the data can be interpolated to a common value.

* HISTORY:
Date      		By	Comments
----------		---	---------------------------------------------------------
10-12-2023		AW	restructoring interpolation
15-05-2023		AW	expansion to specific class extension and adding enums
26-04-2023		AW	expansion to include additional classes
09-12-2022		AW	creation


"""
# Futures
from __future__ import print_function

# standard Libs
import sys

# Specific Imports
from dataclasses import dataclass, field
from enum import Enum, auto

# from typing import Union
from timeit import default_timer as timer

# from tabulate import tabulate
from icecream import ic

# Libs
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pendulum

__author__ = r"Alexander Waringer"
__version__ = r"0.0.1"
__email__ = r"a.waringer@gmx.at"
__status__ = r"dev_status"
__path__ = r"import_data.py"


class ImportType(Enum):
    """Definition Import Type Flag"""

    WEATHER = auto()
    LOAD_PROFILE = auto()
    USAGE_PROFILE = auto()
    NETWORK = auto()
    COMPONENTS = auto()


class DocumentType(Enum):
    """Definition Import Document Type Flag"""

    XLSX = auto()
    CSV = auto()
    TM2 = auto()
    TM3 = auto()


@dataclass
class ImportData:
    """Import external data for further processing
    Args:
        dirpath (str): contains path to dir
        filename (str): contains file name
        fullpath (str): no init, sum of dirpath and filename
        document_type (DocumentType): defines the file type
        import_flag (ImportType): defines the content type
        data(pd.DataFrame): no manual init, data will loaded post init

    Raises:
        ImportError: return if file can't imported properly

    Returns:
        _len_: count of rows
    """

    dirpath: str
    filename: str
    document_type: DocumentType
    import_flag: ImportType
    timezone: str = field(default=pendulum.now().timezone_name)
    fullpath: str = field(init=False, repr=False)
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        if sys.platform.startswith("win"):
            self.fullpath = self.dirpath + "\\" + self.filename
        elif sys.platform.startswith("linux"):
            self.fullpath = self.dirpath + "/" + self.filename
        else:
            raise SystemError("Can not identify Operating System")

        self.data = self.load(
            fullpath=self.fullpath,
            document_type=self.document_type,
            import_flag=self.import_flag,
        )

    def __len__(self) -> None:
        return self.data.shape[0]

    def load(
        self, fullpath: str, document_type: DocumentType, import_flag: ImportType
    ) -> pd.DataFrame:
        """load information into pandas dataframe

        Args:
            fullpath (str): path to file
            document_type (DocumentType): define document type
            import_flag (ImportType): define import type

        Raises:
            ImportError: return if file can't imported properly

        Returns:
            pd.DataFrame: data
        """
        if document_type == DocumentType.XLSX:
            df = pd.read_excel(io=fullpath)
        elif document_type == DocumentType.CSV:
            df = pd.read_csv(fullpath, delimiter=";", decimal=",")
        else:
            raise ImportError("File not in Excel (xlsx or csv) format")

        if import_flag == ImportType.WEATHER:
            df = WeatherImport(df, self.timezone).data
        elif import_flag == ImportType.LOAD_PROFILE:
            df = LoadProfileImport(df, self.timezone).data
        elif import_flag == ImportType.USAGE_PROFILE:
            df = UsageProfileImport(df).data
        elif import_flag == ImportType.COMPONENTS:
            df = ComponentImport(df).data
        elif import_flag == ImportType.NETWORK:
            df = NetworkImport(df).data
        else:
            raise ImportError("Definition of Document Type is not set.")

        return df

    # def load_xlsx(self, fullpath: str, import_flag: ImportType) -> pd.DataFrame:
    #     """load external excel information to dataframe
    #     and set the dtype objects for pandas processing

    #     Args:
    #         fullpath (str): path to file
    #         import_flag (ImportType): define import type

    #     Returns:
    #         pd.DataFrame: imported data is returned as a dataframe
    #     """
    #     df = pd.read_excel(io=fullpath)

    #     if import_flag == ImportType.WEATHER:
    #         df = WeatherImport(df, self.timezone)
    #     elif import_flag == ImportType.LOAD_PROFILE:
    #         df = LoadProfilImport(df, self.timezone)

    #     else:
    #         raise ImportError("Definition of Document Type is not set.")

    #     return df

    # def load_csv(self, fullpath: str, import_flag: ImportType) -> pd.DataFrame:
    #     """load external csv information to dataframe
    #     Work in Progress

    #     Args:
    #         fullpath (str): path to file

    #     Returns:
    #         pd.DataFrame: imported data is returned as a dataframe
    #     """
    #     df = pd.read_csv(fullpath, delimiter=";", decimal=",")
    #     if import_flag == ImportType.COMPONENTS:
    #         df = ComponentImport(df)
    #     elif import_flag == ImportType.NETWORK:
    #         df = NetworkImport(df)
    #     else:
    #         raise ImportError("Definition of Document Type is not set.")

    #     return df


@dataclass
class InterpolateData:
    """this module interpolates data from inheriteded classes
    Args:
        source_data (ImportData): inheritance data for transformation
        compared_data (ImportData): inheritance data target length
        data (pd.DataFrame): no manual init, data will loaded post init

    Returns:
        _len_: count of rows
    """

    source_data: pd.DataFrame
    compared_data: pd.DataFrame
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.data = self.interpolate(
            df_source_data=self.source_data,
            df_compared_data=self.compared_data,
        )

    def __len__(self) -> None:
        return self.data.shape[0]

    def interpolate(
        self, df_source_data: pd.DataFrame, df_compared_data: pd.DataFrame
    ) -> pd.DataFrame:
        """the method interpolate two given dataframes for the same length

        Args:
            df_source_data (pd.DataFrame): source dataframe to adept the current length
            df_compared_data (pd.DataFrame): target length dataframe

        Returns:
            pd.DataFrame: corrected length and time indezes dataframe
        """
        row_sum = [df_source_data.shape[0], df_compared_data.shape[0]]

        # calculate time offset and start date
        # pass it to __build_new_frameset function
        time_range = int(max(row_sum) / row_sum[0])
        if (time_range > 1) and (df_source_data["datetime"][0].hour > 0):
            start_source = df_source_data["datetime"][0].hour * time_range
            df_interpolated = self.build_new_frameset(
                source=df_source_data, offset=time_range, start_value=start_source - 1
            )
        elif (time_range > 1) and (df_source_data["datetime"][0].hour == 0):
            df_interpolated = self.build_new_frameset(
                source=df_source_data, offset=time_range
            )

        df_interpolated["outside_temperature"].interpolate(
            method="polynomial", order=3, axis=0, inplace=True
        )
        df_interpolated["outside_humidity"].interpolate(
            method="polynomial", order=3, axis=0, inplace=True
        )
        return df_interpolated

    def build_new_frameset(
        self, source: pd.DataFrame, offset: int, start_value: int = 0
    ) -> pd.DataFrame:
        """the method build a new frameset for interpolating the data correctly

        Args:
            source (pd.DataFrame): source dataframe for calculation of the new timespans
            offset (int): factor for split an hour (i.e. offset 4 = every 15 min)
            start_value (int, optional): start time value in hours. Defaults to 0.

        Returns:
            pd.DataFrame: corrected length for further processing
        """
        new_index = pd.RangeIndex(len(source) * offset)
        df = pd.DataFrame(np.nan, index=new_index, columns=source.columns)
        ids = np.arange(start_value, len(df), offset)
        df.loc[ids] = source.values  # set initial values to correct index

        # create new datetime structure
        dt = int(60 / offset)
        if start_value > 0:
            offset_datetime = pd.Timedelta(
                hours=df["datetime"][start_value].hour - 1, minutes=60 - dt
            )
            start_datetime = df["datetime"][start_value] - offset_datetime
        elif start_value == 0:
            start_datetime = df["datetime"][start_value]

        # end_datetime = df["datetime"][len(df) - 1].replace(tzinfo=None) + pd.Timedelta(
        end_datetime = df["datetime"][len(df) - 1] + pd.Timedelta(minutes=dt)
        new_datetime = np.arange(
            start_datetime,
            end_datetime,
            pd.Timedelta(minutes=dt),
            dtype="datetime64[s]",
        )
        df["datetime"] = new_datetime

        # set first row to first valid value
        idx, _ = np.where(df.isna())
        if all(idx[0 : df.shape[1] - 1] == 0):
            idr = df.notna().idxmax()
            idr = min(idr[0 : len(idr) - 1])
            # 0 = outside_temperature
            # 1 = outside_humidity
            # 2 = datetime
            df.loc[idx[0]] = [df.loc[idr][0], df.loc[idr][1], df.loc[idr][2]]

        # apply timezone information from source data to new dataframe
        timezone = source.datetime[0].tzinfo.key
        df["datetime"] = [pendulum.instance(x, tz=timezone) for x in df["datetime"]]

        return df


@dataclass
class WeatherImport:
    """import weather information and the clean the export"""

    source: pd.DataFrame
    timezone: str
    column_export: list = field(default_factory=list)
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.set_default()
        df_with_dtypes = self.__set_dtypes(self.source)
        self.data = self.__clean_data_export(df_with_dtypes, self.column_export)

    def set_default(self) -> None:
        """store default values"""
        if not self.column_export:
            self.column_export = ["datetime", "outside_temperature", "outside_humidity"]

    def __set_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        # set the propper dtype for pandas
        df["datetime"] = [
            pendulum.datetime(
                x.year, x.month, x.day, y.hour, y.minute, tz=self.timezone
            )
            for x, y in zip(df["Date"], df["HH:MM"])
        ]
        return df

    def __clean_data_export(
        self, df: pd.DataFrame, column_export: list
    ) -> pd.DataFrame:
        df.drop(columns=df.columns.difference(column_export), inplace=True)
        return df


@dataclass
class LoadProfileImport:
    """instance the proper dtypes for pandas"""

    source: pd.DataFrame
    timezone: str
    first_row: int = field(default=11)
    column_export: list = field(default_factory=list)
    column_keep: list = field(default_factory=list)
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks for the class.

        This method sets the default values, transforms the data, and sets the data types.

        Parameters:
        - self: The instance of the class.

        Returns:
        - None
        """
        self.set_default()
        transformed_df = self.__transform_data(
            self.source, self.first_row, self.column_keep, self.column_export
        )
        self.data = self.__set_dtypes(transformed_df)

    def set_default(self) -> None:
        """
        Store default values.

        This method sets default values for the `column_export` and `column_keep` attributes \
            if they are not already set.
        The `column_export` attribute is set to ["datetime", "demand_load", "demand_energy"] \
            by default.
        The `column_keep` attribute is set to [11, 18, 19] by default.
        """
        if not self.column_export:
            self.column_export = ["datetime", "demand_load", "demand_energy"]
        if not self.column_keep:
            self.column_keep = [11, 18, 19]

    def __transform_data(
        self, df: pd.DataFrame, first_row: int, column_keep: list, column_export: list
    ) -> pd.DataFrame:
        """
        Transforms the given DataFrame by selecting specific columns and renaming them.

        Args:
            df (pd.DataFrame): The input DataFrame.
            first_row (int): The index of the first row to include in the transformed DataFrame.
            column_keep (list): The list of column indices to keep in the transformed DataFrame.
            column_export (list): The list of column names to assign to the kept columns.

        Returns:
            pd.DataFrame: The transformed DataFrame.
        """
        df = df.iloc[first_row:, column_keep].set_axis(column_export, axis=1)
        df.reset_index(drop=True, inplace=True)
        return df

    def __set_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Set the proper data types for the columns in the DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to modify.

        Returns:
            pd.DataFrame: The modified DataFrame with updated data types.
        """
        # set the proper dtype for pandas
        df["datetime"] = [
            pendulum.instance(x, tz=self.timezone) for x in df["datetime"]
        ]
        df["demand_load"] = pd.to_numeric(df["demand_load"])
        df["demand_energy"] = pd.to_numeric(df["demand_energy"])

        return df


@dataclass
class UsageProfileImport:
    """
    Class for importing and processing usage profile data.

    Attributes:
        source (pd.DataFrame): The source DataFrame containing the usage profile data.
        data (pd.DataFrame): The processed DataFrame with the converted values.

    Methods:
        __post_init__(): Perform post-initialization tasks for the object.
        __convert_percentage(column_name: str = "usage [%]") -> pd.DataFrame: Converts the\
              values in the specified column from percentage to decimal format.
    """

    source: pd.DataFrame
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        """
        Perform post-initialization tasks for the object.

        This method converts the data to percentage format.

        Returns:
            None
        """
        self.data = self.__convert_percentage()

    def __convert_percentage(self, column_name: str = "usage [%]") -> pd.DataFrame:
        """
        Converts the values in the specified column from percentage to decimal format.

        Args:
            column_name (str): The name of the column to be converted. Default is "usage [%]".

        Returns:
            pd.DataFrame: The modified DataFrame with the converted values.
        """
        self.source[column_name] = self.source[column_name] / 100
        return self.source


@dataclass
class NetworkImport:
    """import network information and the clean the export"""

    source: pd.DataFrame
    column_list: list = field(default_factory=list)
    column_dict: dict = field(default_factory=dict)
    column_export: list = field(default_factory=list)
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.set_default()
        filtered_df = self.__filter_dataframe(
            self.source, self.column_list, self.column_dict
        )
        self.data = self.__clean_data_export(filtered_df, self.column_export)

    def set_default(self) -> None:
        """store default values"""
        if not self.column_list:
            self.column_list = [
                "EdgeID",
                "Name",
                "Source",
                "Target",
                "SourceName",
                "TargetName",
            ]
        if not self.column_dict:
            self.column_dict = {
                "EdgeID": "edgeid",
                "Source": "parent",
                "Target": "child",
            }
        if not self.column_export:
            self.column_export = [
                "edgeid",
                "parent",
                "child",
            ]

    def __filter_dataframe(
        self, df: pd.DataFrame, column_list: list, column_dict: dict
    ) -> pd.DataFrame:
        """filter unneccessary information

        Args:
            df (pd.DataFrame): dataframe source for transformation
            column_list (list): list of vital columns
            column_dict (dict): renaming the columns with a dict

        Returns:
            pd.DataFrame: filtered dataframe
        """
        df = df[column_list]
        df.rename(columns=column_dict, inplace=True)
        return df

    def __clean_data_export(
        self, df: pd.DataFrame, column_export: list
    ) -> pd.DataFrame:
        """filtering the relevant information

        Args:
            df (pd.DataFrame): dataframe for transformation
            column_export (list): list of column names to filter

        Returns:
            pd.DataFrame: optimized dataframe
        """
        return df[column_export]


@dataclass
class ComponentImport:
    """standardized outputs must be made possible by importing the individual components

    Args:
        source (pd.DataFrame): database as dataframe
        column_list (list): list of vital columns of source
        column_dict (dict): renaming the columns of df with a dict
        column_check (dict): define the form, based on dimensions
        column_export (list): list of column names to filter for exporting df
        rectangled_info (dict): additional information for rectangle processing
        reduction_info (dict): additional information for reduction processing

    Raises:
        ValueError: raises if verification error occurs

    """

    source: pd.DataFrame
    column_list: list = field(default_factory=list)
    column_dict: dict = field(default_factory=dict)
    column_check: dict = field(default_factory=dict)
    column_export: list = field(default_factory=list)
    rectangled_info: dict = field(default_factory=dict)
    reduction_info: dict = field(default_factory=dict)
    pd_dtypes: dict = field(default_factory=dict)
    data: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        self.set_default()
        filtered_df = self.__filter_dataframe(
            self.source, self.column_list, self.column_dict
        )
        builded_df = self.__build_network(
            filtered_df, self.column_check, self.rectangled_info, self.reduction_info
        )
        dtyped_df = self.__set_dtypes(builded_df, self.pd_dtypes)
        self.data = self.__clean_data_export(dtyped_df, self.column_export)

    def set_default(self) -> None:
        """store default values"""
        if not self.column_list:
            self.column_list = [
                "NodeID",
                "component type",
                "System",
                "diameter in mm",
                "width in mm",
                "height in mm",
                "diameter inlet in mm",
                "diameter outlet in mm",
                "width inlet in mm",
                "height inlet in mm",
                "width outlet in mm",
                "height outlet in mm",
                "deflection angle in degrees",
                "Length",
            ]
        if not self.column_dict:
            self.column_dict = {
                "NodeID": "nodeid",
                "component type": "component",
                "System": "system",
                "diameter in mm": "diameter",
                "width in mm": "width",
                "height in mm": "height",
                "diameter inlet in mm": "diameter_in",
                "diameter outlet in mm": "diameter_out",
                "width inlet in mm": "width_in",
                "height inlet in mm": "height_in",
                "width outlet in mm": "width_out",
                "height outlet in mm": "height_out",
                "deflection angle in degrees": "angle",
                "Length": "length",
            }
        if not self.column_check:
            self.column_check = {
                "diameter": "circled",
                "width": "rectangled",
                "diameter_in": "reduction",
                "width_in": "reduction",
            }
        if not self.rectangled_info:
            self.rectangled_info = {"width": "height"}
        if not self.reduction_info:
            self.reduction_info = {
                "diameter_in": [
                    "diameter_in",
                    "diameter_out",
                    "width_out",
                    "height_out",
                ],
                "width_in": [
                    "width_in",
                    "height_in",
                    "diameter_out",
                    "width_out",
                    "height_out",
                ],
            }

        if not self.column_export:
            self.column_export = [
                "nodeid",
                "component",
                "form",
                "system",
                "dimension",
                "angle",
                "length",
            ]
        if not self.pd_dtypes:
            self.pd_dtypes = {
                "component": str,
                "form": str,
                "system": str,
                "dimension": str,
            }

    def __filter_dataframe(
        self, df: pd.DataFrame, column_list: list, column_dict: dict
    ) -> pd.DataFrame:
        """filter unneccessary information

        Args:
            df (pd.DataFrame): dataframe source for transformation
            column_list (list): list of vital columns
            column_dict (dict): renaming the columns with a dict

        Returns:
            pd.DataFrame: filtered dataframe
        """
        df = df[column_list]
        df.rename(columns=column_dict, inplace=True)
        return df

    def __build_network(
        self,
        df: pd.DataFrame,
        columns_check: dict,
        rectangled_info: dict,
        reduction_info: dict,
    ) -> pd.DataFrame:
        """the dimensions and shape of the components are transformed
        into a standardized format

        Args:
            df (pd.DataFrame): dataframe source for transformation
            columns_check (dict): define the form, based on dimensions
            rectangled_info (dict): additional information for rectangle processing
            reduction_info (dict): additional information for reduction processing

        Raises:
            ValueError: raises if verification error occurs

        Returns:
            pd.DataFrame: transformed dataframe
        """

        df.assign(dimension=None, form=None)

        for column, form_type in columns_check.items():
            valid_values = df[column].notna()

            if form_type == "circled":
                df.loc[valid_values, "dimension"] = df.loc[valid_values, column].astype(
                    str
                )
                df.loc[valid_values, "form"] = form_type

            elif form_type == "rectangled":
                df.loc[valid_values, "dimension"] = (
                    df.loc[valid_values, column].astype(str)
                    + "x"
                    + df.loc[valid_values, rectangled_info[column]].astype(str)
                )
                df.loc[valid_values, "form"] = form_type

                room_check = df["system"] == "ROOM"
                df.loc[room_check, "form"] = "room"

            elif form_type == "reduction":
                df.loc[valid_values, "dimension"] = df[df[valid_values].notna()][
                    reduction_info[column]
                ].apply(
                    lambda row: "-".join([str(val) for val in row.dropna()]), axis=1
                )
                df.loc[valid_values, "form"] = form_type

            # verification of result
            nan_values = df.loc[valid_values, "dimension"].isna()
            check_values = valid_values[valid_values] != nan_values
            false_indices = [
                index for index, value in enumerate(check_values) if not value
            ]

            if false_indices:
                raise ValueError(
                    f"Check failed for {len(false_indices)} items; {false_indices}"
                )

        return df

    def __set_dtypes(self, df: pd.DataFrame, assign_dtype: dict) -> pd.DataFrame:
        for column, dtype_type in assign_dtype.items():
            df[column] = df[column].astype(dtype_type)

        return df

    def __clean_data_export(
        self, df: pd.DataFrame, column_export: list
    ) -> pd.DataFrame:
        """filtering the relevant information

        Args:
            df (pd.DataFrame): dataframe for transformation
            column_export (list): list of column names to filter

        Returns:
            pd.DataFrame: optimized dataframe
        """
        return df[column_export]


@dataclass
class PlotData:
    """Plot data with matplotlib"""

    # imported: Union[ImportData, InterpolateData]
    imported: pd.DataFrame
    save: bool = field(default=False)
    name: str = field(default="plot.png")

    def outside_condition(self) -> None:
        """matplot for the outside conditions"""
        fig, axes = plt.subplots(2, 1, num="outside conditions", figsize=(10, 8))
        plt.style.use("seaborn-notebook")

        x = self.imported["datetime"]
        y1 = self.imported["outside_temperature"]
        ax = axes[0]
        ax.plot(x, y1, "-", color="blue", lw=0.7, label="outside Temperature")
        ax.tick_params(axis="both", labelsize=10, labelrotation=40)
        ax.set_xlabel("time [datetime]")
        ax.set_ylabel("temperature (\u03B8) [°C]")
        ax.set_title("outside temperature")
        ax.set_xlim(
            self.imported["datetime"][0],
            self.imported["datetime"][len(self.imported) - 1],
        )
        ax.set_ylim(
            round(self.imported["outside_temperature"].min()) - 2,
            round(self.imported["outside_temperature"].max()) + 2,
        )
        ax.grid(color="black", linestyle="-.", linewidth=0.3)
        fig.suptitle(
            f"outside conditions in {self.imported['datetime'][0].year}",
            fontsize=16,
        )

        y2 = self.imported["outside_humidity"]
        ax = axes[1]
        ax.plot(x, y2, "-", color="red", lw=0.7, label="outside humidity")
        ax.tick_params(axis="both", labelsize=10, labelrotation=40)
        ax.set_xlabel("time [datetime]")
        ax.set_ylabel("rel. humidity (\u03C6) [%]")
        ax.set_title("outside humidity")
        ax.set_xlim(
            self.imported["datetime"][0],
            self.imported["datetime"][len(self.imported) - 1],
        )
        ax.set_ylim(0, 100)
        ax.grid(color="black", linestyle="-.", linewidth=0.3)

        fig.tight_layout()
        if self.save:
            plt.savefig(self.name, dpi=200)
        plt.show()


if __name__ == "__main__":
    start = timer()
    # weather_raw = ImportData(
    #     dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
    #     filename="LV_Madrid.xlsx",
    #     document_type=DocumentType.XLSX,
    #     import_flag=ImportType.WEATHER,
    # )
    # load = ImportData(
    #     dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
    #     filename="GGV_SLP_1000_MWh_2021_01-2020-09-24.xlsx",
    #     document_type=DocumentType.XLSX,
    #     import_flag=ImportType.LOAD_PROFILE,
    # )
    # ic(load.data.head())
    # ic(load.data.dtypes)
    # weather = InterpolateData(weather_raw, load)
    # ic(weather.data.dtypes)
    # ic(weather.data.shape)
    # ic(weather_raw.data.shape)
    # ic(load.data.shape)

    # PlotData(weather).outside_condition()
    # --------------------------------------------------------------------------------

    # edges = ImportData(
    #     dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
    #     filename="Edges.csv",
    #     document_type=DocumentType.CSV,
    #     import_flag=ImportType.NETWORK,
    # )
    # vertices = ImportData(
    #     dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
    #     filename="Vertices.csv",
    #     document_type=DocumentType.CSV,
    #     import_flag=ImportType.NETWORK,
    # ).data
    # base_network = ComponentImport(vertices).data
    # ic(base_network)
    # test = MergeHVACNetwork(vertices, edges)
    usage = ImportData(
        dirpath="D:\\GitHub\\masterthesis\\masterthesis\\import",
        filename="usage_profile.xlsx",
        document_type=DocumentType.XLSX,
        import_flag=ImportType.USAGE_PROFILE,
    )
    ic(usage.data.head())
    end = timer()
    ic(end - start)
