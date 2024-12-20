import requests
from pathlib import Path
import ephem
import pandas as pd
import os
import json


# run script with: 
#       python3 horizons_nasa_data.py


# Planet encodings for the JPL Horizons API
planets = {
    "Mercury": "199",
    "Venus": "299",
    "Earth": "399",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
    "Pluto": "999"
}

# Check if the start date is valid for retrieving ephemerides data for a specific planet.
def check_start_date_ephem_by_planet(start_date, planet):
    ephemerides_startdate_by_planet = {
        "Mercury": "-4000-01-01",
        "Venus": "-4000-01-01",
        "Earth": "-4000-01-01",
        "Mars": "1600-01-02",
        "Jupiter": "1600-01-11",
        "Saturn": "1749-12-31",
        "Uranus": "1599-12-15",
        "Neptune": "1600-01-15",
        "Pluto": "1700-01-07"
    }
    start_date_dt = ephem.Date(start_date)
    if ephemerides_startdate_by_planet[planet]:
        start_date_ephem_dt = ephem.Date(ephemerides_startdate_by_planet[planet])

        if start_date_dt < start_date_ephem_dt:
            return False
        else:
            return True
        



# Convert a Julian date to a formatted date string
# A Julian date (JD) is a continuous count of days and fractions of a day 
# since noon (12:00 PM) on January 1, 4713 BCE, in the Julian calendar.
def convert_from_juliandate(julian_date):
    date_ephem = ephem.date(julian_date - 2415020)
    date_str = str(date_ephem).split()[0]
    year, month, day = map(int, date_str.split('/'))
    if str(year).startswith("-"):
        date_formatted = f"{year:05d}-{month:02d}-{day:02d}"
    else:
        date_formatted = f"{year:04d}-{month:02d}-{day:02d}"
    return date_formatted

# Convert a formatted date string to a Julian date
def convert_to_juliandate(date):
    jd = ephem.julian_date(date)
    return jd


# Get planet positions from the Sun in CSV format
def get_planet_positions_from_sun_csv(start_date, end_date, time_step, planet, output_folder):

    url = 'https://ssd.jpl.nasa.gov/api/horizons.api'

    param = {
        "format": "text",
        "COMMAND": planets[planet],
        "OBJ_DATA": "YES",
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "VECTORS",
        "CENTER": "@sun",
        "START_TIME": f"JD{str(convert_to_juliandate(start_date))}",
        "STOP_TIME": f"JD{str(convert_to_juliandate(end_date))}",
        "STEP_SIZE": time_step,
        "CSV_FORMAT": "YES"
    }

    ephem_exists = check_start_date_ephem_by_planet(start_date, planet)

    if ephem_exists:
        response = requests.get(url, params=param)
        content_txt = response.text

        start = content_txt.find("$$SOE")
        end = content_txt.find("$$EOE")

        data = content_txt[start + len("$$EOE"):end]

        # Eliminar la coma al final de cada línea
        cleaned_data = '\n'.join(line.strip(',') for line in data.split('\n'))

        file_path = Path(output_folder) / f"{planet}_{start_date}_{end_date}.csv"

        with open(file_path, 'w', encoding="utf-8") as file:
            file.write(cleaned_data)
        print(f"Data of '{planet}' saved to {file_path}")
    else:
        print(f"No ephemeris for target '{planet}' for date {start_date}")


# Get planet positions from the Sun in CSV format for multiple planets
def get_multiple_planet_position_from_sun(start_date, end_date, time_step, output_folder):
    for planet in planets:
        get_planet_positions_from_sun_csv(start_date, end_date, time_step, planet, output_folder)


class CompactVectorJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        # Customize encoding for lists with three elements (vectors)
        if isinstance(obj, list) and len(obj) == 3:
            return f"[{obj[0]}, {obj[1]}, {obj[2]}]"
        return super().encode(obj)

class OneLineVectorJSONEncoder(json.JSONEncoder):
    def iterencode(self, obj, _one_shot=False):
        """
        Custom encoder to ensure vectors (lists of 3 elements) appear on one line.
        """
        if isinstance(obj, list) and len(obj) == 3 and all(isinstance(x, (int, float)) for x in obj):
            # Format vector components compactly on a single row
            return f"[{obj[0]}, {obj[1]}, {obj[2]}]"
        # Fall back to default handling
        return super().iterencode(obj, _one_shot=_one_shot)
    

def format_vectors(data):
    """
    Recursively process the dictionary to ensure that lists of three numbers
    (vectors) are converted to single-line strings.
    """
    if isinstance(data, dict):
        return {k: format_vectors(v) for k, v in data.items()}
    elif isinstance(data, list) and len(data) == 3 and all(isinstance(x, (int, float)) for x in data):
        # Convert vector to a single-line string
        return f"[{data[0]}, {data[1]}, {data[2]}]"
    return data



# Create a JSON file with the planet positions from the CSV files
def create_assembled_data(csv_folder, output_folder):
    planet_position_dict = {}

    # Ensure the output folder exists
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    col_names = {
        0: "date_julian",
        1: "date_calendar",
        2: "position_x",
        3: "position_y",
        4: "position_z",
        5: "velocity_x",
        6: "velocity_y",
        7: "velocity_z",
        8: "light_time",
        9: "range_geocentric",
        10: "range_radial"
    }

    for csv_file in os.listdir(csv_folder):
        if csv_file.endswith(".csv"):
            planet = csv_file.split("_")[0]

            path = f"{csv_folder}/{csv_file}"
            try:
                df = pd.read_csv(path, sep=",", header=None)
                df = df.rename(columns=col_names)

                for _, row in df.iterrows():
                    date = convert_from_juliandate(row["date_julian"])

                    if date not in planet_position_dict:
                        planet_position_dict[date] = {}

                    planet_position_dict[date][planet] = [row["position_x"], row["position_y"], row["position_z"]]
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")

    formatted_data = format_vectors(planet_position_dict)

    output_path = Path(output_folder) / "planet_positions_assembled.json"
    
    with open(output_path, "w") as json_file:
        json.dump(planet_position_dict, json_file,indent=2,cls=OneLineVectorJSONEncoder)
    print(f"Combined data saved to {output_path}")


# Final Function that makes everything
def get_data():
    # Get the data for the planets from the Sun
    #get_multiple_planet_position_from_sun(start_date="1800-01-03", end_date="2099-12-31", time_step="2d", output_folder="./data/planet_data_modified")
    get_multiple_planet_position_from_sun(start_date="1800-01-01", end_date="1899-12-31", time_step="1d", output_folder="./data/planet_data_modified")
    # Create the assembled data
    create_assembled_data("./data/planet_data_modified", "./data/planet_data_assembled")

    print(f"Got data from 1800-01-03 to 2099-12-31")



# --------------------------- DATA EXTRACTION ---------------------------

get_data()










#get_multiple_planet_position_from_sun(start_date="1800-01-03", end_date="2099-12-31", time_step="5d", output_folder="./data/planet_data_modified")
#create_assembled_data("./data/planet_data_modified","./data/planet_data_assembled")

#get_planet_positions_from_sun_csv(
#     "0001-01-01", "0499-12-31", "1y", "Earth", "./data")

# Getting data BC
#get_multiple_planet_position_from_sun(
#     start_date="-2000-01-01", end_date="-0001-12-31", time_step="10d", output_folder="./data/bc/2000-0001_10d")

# Getting data AC
#get_multiple_planet_position_from_sun(
#    start_date="1751-01-01", end_date="2099-12-31", time_step="5d", output_folder="./data/ac/1751-2099_5d")

#create_json_file_with_planet_positions_from_csv_files("./data/ac/1751-2099_5d")


