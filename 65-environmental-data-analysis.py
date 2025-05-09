import base64
import getpass
import io
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Fix os.getlogin for environments that might have issues
os.getlogin = getpass.getuser

from mcp.sampling import SamplingMessage, TextContent
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolError

# Create an MCP server
mcp = FastMCP("Environmental Data Analysis")


# Simulated environmental data
class EnvironmentalDataSimulator:
    def __init__(self):
        # Locations with simulated data
        self.locations = [
            "New York",
            "Los Angeles",
            "Chicago",
            "Miami",
            "Denver",
            "Seattle",
        ]

        # Data types available
        self.data_types = [
            "temperature",
            "precipitation",
            "air_quality",
            "humidity",
            "wind_speed",
        ]

        # Generate date range for the past year
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=365)
        self.date_range = pd.date_range(self.start_date, self.end_date, freq="D")

        # Initialize the dataset
        self.generate_data()

        # Track chart history
        self.charts = {}
        self.chart_counter = 0

    def generate_data(self):
        """Generate simulated environmental data for all locations"""
        self.data = {}

        # Base parameters for different locations
        location_params = {
            "New York": {
                "temperature": {"mean": 15, "amplitude": 15, "noise": 3},
                "precipitation": {"mean": 3, "amplitude": 2, "noise": 1},
                "air_quality": {"mean": 50, "amplitude": 20, "noise": 10},
                "humidity": {"mean": 65, "amplitude": 15, "noise": 8},
                "wind_speed": {"mean": 8, "amplitude": 4, "noise": 2},
            },
            "Los Angeles": {
                "temperature": {"mean": 20, "amplitude": 8, "noise": 2},
                "precipitation": {"mean": 1, "amplitude": 2, "noise": 0.5},
                "air_quality": {"mean": 60, "amplitude": 30, "noise": 15},
                "humidity": {"mean": 55, "amplitude": 10, "noise": 5},
                "wind_speed": {"mean": 6, "amplitude": 3, "noise": 1.5},
            },
            "Chicago": {
                "temperature": {"mean": 12, "amplitude": 18, "noise": 4},
                "precipitation": {"mean": 2.5, "amplitude": 2, "noise": 1},
                "air_quality": {"mean": 45, "amplitude": 15, "noise": 8},
                "humidity": {"mean": 70, "amplitude": 15, "noise": 7},
                "wind_speed": {"mean": 10, "amplitude": 5, "noise": 2.5},
            },
            "Miami": {
                "temperature": {"mean": 25, "amplitude": 5, "noise": 2},
                "precipitation": {"mean": 4, "amplitude": 3, "noise": 1.5},
                "air_quality": {"mean": 40, "amplitude": 15, "noise": 7},
                "humidity": {"mean": 80, "amplitude": 10, "noise": 5},
                "wind_speed": {"mean": 7, "amplitude": 3, "noise": 1.5},
            },
            "Denver": {
                "temperature": {"mean": 10, "amplitude": 15, "noise": 3},
                "precipitation": {"mean": 1.5, "amplitude": 1, "noise": 0.5},
                "air_quality": {"mean": 35, "amplitude": 10, "noise": 5},
                "humidity": {"mean": 45, "amplitude": 15, "noise": 7},
                "wind_speed": {"mean": 9, "amplitude": 4, "noise": 2},
            },
            "Seattle": {
                "temperature": {"mean": 12, "amplitude": 10, "noise": 2},
                "precipitation": {"mean": 3.5, "amplitude": 2, "noise": 1},
                "air_quality": {"mean": 30, "amplitude": 10, "noise": 5},
                "humidity": {"mean": 75, "amplitude": 10, "noise": 5},
                "wind_speed": {"mean": 7, "amplitude": 3, "noise": 1.5},
            },
        }

        # Generate time-series data for each location and data type
        for location in self.locations:
            self.data[location] = {}
            params = location_params[location]

            for data_type in self.data_types:
                param = params[data_type]
                mean = param["mean"]
                amplitude = param["amplitude"]
                noise = param["noise"]

                # Generate seasonal data with noise
                days = np.arange(len(self.date_range))
                seasonal_component = amplitude * np.sin(2 * np.pi * days / 365)
                noise_component = np.random.normal(0, noise, len(days))

                # Combine components
                values = mean + seasonal_component + noise_component

                # Ensure non-negative values for certain data types
                if data_type in [
                    "precipitation",
                    "air_quality",
                    "humidity",
                    "wind_speed",
                ]:
                    values = np.maximum(values, 0)

                # Store as a pandas Series
                self.data[location][data_type] = pd.Series(
                    values, index=self.date_range
                )

    def get_locations(self) -> List[str]:
        """Get all available locations"""
        return self.locations

    def get_data_types(self) -> List[str]:
        """Get all available data types"""
        return self.data_types

    def get_data(
        self,
        location: str,
        data_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """Get data for a specific location and data type within a date range"""
        if location not in self.locations:
            return {
                "error": f"Location '{location}' not found. Available locations: {', '.join(self.locations)}"
            }

        if data_type not in self.data_types:
            return {
                "error": f"Data type '{data_type}' not found. Available types: {', '.join(self.data_types)}"
            }

        # Get the data series
        data_series = self.data[location][data_type]

        # Apply date filters if provided
        start = pd.to_datetime(start_date) if start_date else self.start_date
        end = pd.to_datetime(end_date) if end_date else self.end_date

        # Slice the data
        filtered_data = data_series[
            (data_series.index >= start) & (data_series.index <= end)
        ]

        # Format the result
        result = {
            "location": location,
            "data_type": data_type,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "unit": self.get_unit(data_type),
            "data": {
                date.strftime("%Y-%m-%d"): value
                for date, value in filtered_data.items()
            },
        }

        return result

    def get_unit(self, data_type: str) -> str:
        """Get the unit for a specific data type"""
        units = {
            "temperature": "°C",
            "precipitation": "mm",
            "air_quality": "AQI",
            "humidity": "%",
            "wind_speed": "m/s",
        }
        return units.get(data_type, "")

    def create_chart(
        self,
        location: str,
        data_types: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        chart_type: str = "line",
    ) -> Dict:
        """Create a chart for specific data types at a location"""
        # Validate location
        if location not in self.locations:
            return {
                "error": f"Location '{location}' not found. Available locations: {', '.join(self.locations)}"
            }

        # Validate data types
        invalid_types = [dt for dt in data_types if dt not in self.data_types]
        if invalid_types:
            return {
                "error": f"Invalid data types: {', '.join(invalid_types)}. Available types: {', '.join(self.data_types)}"
            }

        # Apply date filters
        start = pd.to_datetime(start_date) if start_date else self.start_date
        end = pd.to_datetime(end_date) if end_date else self.end_date

        # Create figure and axis
        plt.figure(figsize=(10, 6))

        # Plot each data type
        for data_type in data_types:
            data_series = self.data[location][data_type]
            filtered_data = data_series[
                (data_series.index >= start) & (data_series.index <= end)
            ]

            if chart_type == "line":
                plt.plot(
                    filtered_data.index,
                    filtered_data.values,
                    label=f"{data_type} ({self.get_unit(data_type)})",
                )
            elif chart_type == "bar":
                plt.bar(
                    filtered_data.index,
                    filtered_data.values,
                    label=f"{data_type} ({self.get_unit(data_type)})",
                    alpha=0.7,
                )
            else:
                plt.close()
                return {
                    "error": f"Chart type '{chart_type}' not supported. Use 'line' or 'bar'."
                }

        # Set title and labels
        plt.title(
            f"{', '.join(data_types)} in {location} ({start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')})"
        )
        plt.xlabel("Date")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True)

        # Save the figure to a base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close()

        # Generate a chart ID
        self.chart_counter += 1
        chart_id = f"chart_{self.chart_counter}"

        # Store the chart
        self.charts[chart_id] = {
            "location": location,
            "data_types": data_types,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "chart_type": chart_type,
            "image_base64": image_base64,
        }

        return {
            "chart_id": chart_id,
            "location": location,
            "data_types": data_types,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "chart_type": chart_type,
        }

    def get_chart(self, chart_id: str) -> Dict:
        """Get a previously created chart by ID"""
        if chart_id not in self.charts:
            return {"error": f"Chart with ID '{chart_id}' not found"}

        return self.charts[chart_id]

    def analyze_trends(
        self,
        location: str,
        data_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """Analyze trends for a specific data type at a location"""
        # Get the data
        data_result = self.get_data(location, data_type, start_date, end_date)

        # Check for errors
        if "error" in data_result:
            return data_result

        # Convert to pandas Series for analysis
        data_dict = data_result["data"]
        dates = [pd.to_datetime(date) for date in data_dict.keys()]
        values = list(data_dict.values())
        series = pd.Series(values, index=dates)

        # Calculate statistics
        mean = series.mean()
        median = series.median()
        std_dev = series.std()
        min_val = series.min()
        max_val = series.max()

        # Calculate trend (simple linear regression)
        x = np.arange(len(series))
        y = series.values
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        # Determine trend direction
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        # Calculate monthly averages if data spans multiple months
        monthly_avg = series.resample("M").mean().to_dict()
        monthly_avg = {k.strftime("%Y-%m"): v for k, v in monthly_avg.items()}

        return {
            "location": location,
            "data_type": data_type,
            "unit": data_result["unit"],
            "period": f"{data_result['start_date']} to {data_result['end_date']}",
            "statistics": {
                "mean": mean,
                "median": median,
                "std_dev": std_dev,
                "min": min_val,
                "max": max_val,
            },
            "trend": {"direction": trend, "slope": slope},
            "monthly_averages": monthly_avg,
        }

    def compare_locations(
        self,
        locations: List[str],
        data_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict:
        """Compare a specific data type across multiple locations"""
        # Validate locations
        invalid_locations = [loc for loc in locations if loc not in self.locations]
        if invalid_locations:
            return {
                "error": f"Invalid locations: {', '.join(invalid_locations)}. Available locations: {', '.join(self.locations)}"
            }

        # Validate data type
        if data_type not in self.data_types:
            return {
                "error": f"Data type '{data_type}' not found. Available types: {', '.join(self.data_types)}"
            }

        # Apply date filters
        start = pd.to_datetime(start_date) if start_date else self.start_date
        end = pd.to_datetime(end_date) if end_date else self.end_date

        # Collect data for each location
        location_data = {}
        for location in locations:
            data_series = self.data[location][data_type]
            filtered_data = data_series[
                (data_series.index >= start) & (data_series.index <= end)
            ]
            location_data[location] = {
                "mean": filtered_data.mean(),
                "median": filtered_data.median(),
                "std_dev": filtered_data.std(),
                "min": filtered_data.min(),
                "max": filtered_data.max(),
            }

        # Create comparison chart
        plt.figure(figsize=(12, 6))

        # Set up box plot data
        box_data = [
            self.data[location][data_type][
                (self.data[location][data_type].index >= start)
                & (self.data[location][data_type].index <= end)
            ].values
            for location in locations
        ]

        # Create box plot
        plt.boxplot(box_data, labels=locations)
        plt.title(
            f"Comparison of {data_type} ({self.get_unit(data_type)}) across locations"
        )
        plt.ylabel(f"{data_type} ({self.get_unit(data_type)})")
        plt.grid(True, axis="y")

        # Save the figure to a base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close()

        # Generate a chart ID
        self.chart_counter += 1
        chart_id = f"chart_{self.chart_counter}"

        # Store the chart
        self.charts[chart_id] = {
            "locations": locations,
            "data_type": data_type,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "chart_type": "boxplot",
            "image_base64": image_base64,
        }

        return {
            "data_type": data_type,
            "unit": self.get_unit(data_type),
            "period": f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            "location_data": location_data,
            "comparison_chart_id": chart_id,
        }


# Initialize the data simulator
env_data = EnvironmentalDataSimulator()


# Define MCP tools for environmental data analysis
@mcp.tool()
def get_available_locations() -> List[str]:
    """
    Get a list of all available locations with environmental data

    Returns:
        List of location names
    """
    return env_data.get_locations()


@mcp.tool()
def get_available_data_types() -> List[str]:
    """
    Get a list of all available environmental data types

    Returns:
        List of data type names
    """
    return env_data.get_data_types()


@mcp.tool()
def get_environmental_data(
    location: str,
    data_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """
    Get environmental data for a specific location and data type

    Args:
        location: Name of the location (e.g., "New York")
        data_type: Type of data to retrieve (e.g., "temperature")
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)

    Returns:
        Dictionary with the requested environmental data
    """
    return env_data.get_data(location, data_type, start_date, end_date)


@mcp.tool()
def create_data_chart(
    location: str,
    data_types: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    chart_type: str = "line",
) -> Dict:
    """
    Create a chart visualizing environmental data

    Args:
        location: Name of the location (e.g., "New York")
        data_types: List of data types to include in the chart
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        chart_type: Type of chart ("line" or "bar")

    Returns:
        Dictionary with chart information and ID
    """
    return env_data.create_chart(location, data_types, start_date, end_date, chart_type)


@mcp.tool()
def analyze_data_trends(
    location: str,
    data_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """
    Analyze trends in environmental data

    Args:
        location: Name of the location (e.g., "New York")
        data_type: Type of data to analyze (e.g., "temperature")
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)

    Returns:
        Dictionary with trend analysis results
    """
    return env_data.analyze_trends(location, data_type, start_date, end_date)


@mcp.tool()
def compare_locations_data(
    locations: List[str],
    data_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """
    Compare environmental data across multiple locations

    Args:
        locations: List of location names to compare
        data_type: Type of data to compare (e.g., "temperature")
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)

    Returns:
        Dictionary with comparison results
    """
    return env_data.compare_locations(locations, data_type, start_date, end_date)


# Resources for accessing environmental data
@mcp.resource("env_data://locations")
def resource_get_locations() -> str:
    """Get a list of all available locations"""
    return json.dumps(env_data.get_locations())


@mcp.resource("env_data://data_types")
def resource_get_data_types() -> str:
    """Get a list of all available data types"""
    return json.dumps(env_data.get_data_types())


@mcp.resource("env_data://location/{location}/{data_type}")
def resource_get_data(location: str, data_type: str) -> str:
    """Get environmental data for a specific location and data type"""
    data = env_data.get_data(location, data_type)
    return json.dumps(data)


@mcp.resource("env_data://charts/{chart_id}")
def resource_get_chart(chart_id: str) -> str:
    """Get a previously created chart by ID"""
    chart = env_data.get_chart(chart_id)
    # Only include metadata, not the actual image
    if "error" not in chart:
        # Create a copy without the image data to avoid large resource responses
        chart_meta = {k: v for k, v in chart.items() if k != "image_base64"}
        chart_meta["note"] = "Image data available via get_chart_image tool"
        return json.dumps(chart_meta)
    return json.dumps(chart)


# Tool to get chart image data (since it might be large)
@mcp.tool()
def get_chart_image(chart_id: str) -> Dict:
    """
    Get the image data for a previously created chart

    Args:
        chart_id: ID of the chart to retrieve

    Returns:
        Dictionary with chart information and base64-encoded image
    """
    chart = env_data.get_chart(chart_id)
    if "error" in chart:
        return chart
    return {
        "chart_id": chart_id,
        "image_data": chart["image_base64"],
        "content_type": "image/png",
    }


# Advanced analysis tool using LLM
@mcp.tool()
def interpret_environmental_data(
    location: str,
    data_types: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    """
    Provide an AI interpretation of environmental data trends and patterns

    Args:
        location: Name of the location
        data_types: List of data types to analyze
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)

    Returns:
        Dictionary with interpretation results
    """
    # Validate inputs
    if location not in env_data.get_locations():
        raise ToolError(f"Location '{location}' not found")

    invalid_types = [dt for dt in data_types if dt not in env_data.get_data_types()]
    if invalid_types:
        raise ToolError(f"Invalid data types: {', '.join(invalid_types)}")

    # Collect data for each data type
    data_collection = {}
    for data_type in data_types:
        data_collection[data_type] = env_data.get_data(
            location, data_type, start_date, end_date
        )

    # Create a prompt for the LLM
    prompt = f"""
    Analyze the following environmental data for {location} from {data_collection[data_types[0]]["start_date"]} to {data_collection[data_types[0]]["end_date"]}:
    
    {json.dumps(data_collection, indent=2)}
    
    Please provide:
    1. A summary of the key trends for each data type
    2. Correlations between different data types, if any
    3. Unusual patterns or anomalies in the data
    4. Potential environmental implications of these trends
    5. Recommendations based on this analysis
    """

    # Sample from LLM
    messages = [
        SamplingMessage(
            role="system",
            content=[
                TextContent(
                    "You are an environmental data analyst specializing in interpreting climate and environmental data."
                )
            ],
        ),
        SamplingMessage(role="user", content=[TextContent(prompt)]),
    ]

    sampling = mcp.get_sampling()
    response = sampling.sample(messages=messages)

    # Extract the content from the response
    interpretation = (
        response.message.content[0].text
        if response and response.message and response.message.content
        else "Analysis failed"
    )

    return {
        "location": location,
        "data_types": data_types,
        "period": f"{data_collection[data_types[0]]['start_date']} to {data_collection[data_types[0]]['end_date']}",
        "interpretation": interpretation,
        "timestamp": datetime.now().isoformat(),
    }


# Prompt templates for environmental data analysis
environmental_data_prompt = """
You're now connected to an Environmental Data Analysis tool that lets you analyze climate and environmental data:

Available tools:
- get_available_locations(): Get a list of all available locations
- get_available_data_types(): Get a list of all available data types
- get_environmental_data(location, data_type, start_date, end_date): Get data for a location and type
- create_data_chart(location, data_types, start_date, end_date, chart_type): Create a visualization
- analyze_data_trends(location, data_type, start_date, end_date): Analyze trends in the data
- compare_locations_data(locations, data_type, start_date, end_date): Compare data across locations
- get_chart_image(chart_id): Get the image data for a chart
- interpret_environmental_data(location, data_types, start_date, end_date): Get AI interpretation

Start by exploring available locations and data types, then analyze specific environmental metrics.

Sample workflow:
1. Check available locations and data types
2. Get temperature data for New York
3. Create a chart showing temperature and precipitation
4. Analyze trends in air quality
5. Compare humidity across multiple cities
6. Get an AI interpretation of the environmental patterns

The tool provides historical data for various environmental metrics across major U.S. cities.
"""

mcp.add_prompt_template("environmental_data", environmental_data_prompt)
