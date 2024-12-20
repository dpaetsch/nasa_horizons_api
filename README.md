# nasa_horizons_api

This project was used to fetch data from the JPL Horizons systems, for use in other projects such as (https://github.com/dpaetsch/CosmicClicker/blob/main/README.md)[Cosmic Clicker].

## Modes of Use:
There are two ways of using this:
  1. Fetch Individual Planet Data
  2. Fetch All Planets data and format json into per-date structure.
 
### 1) Fetch Individual Planet Data
1. Change `parameters.txt` to request the specific data you would like to query from JPL Horizons System API.
2. Run `python request.py parameters.txt` and wait for the results to show in `results.txt`

### 2) Fetch All Planets data and format json into per-date structure
1. Open `horizons_nasa_data.py` and change the parameters that you would like to fetch.
2. Run `python horizons_nasa_data.py` and wait for the data to arrive in the `data` folder. (It will first query all of the planets individually, and then put all of the 3D positional data into a single file in a per-date structure).


