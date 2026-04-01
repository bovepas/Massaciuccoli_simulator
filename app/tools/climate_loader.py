"""
Massaciuccoli Digital Twin
Climate Loader (ASC Raster → Lat/Lon Mapping)

Questo modulo:
- legge file .asc (raster)
- costruisce una matrice numpy
- permette di ottenere il valore dato (lat, lon)
"""

import numpy as np


# ======================================================
# ASC READER
# ======================================================

def load_asc(filepath: str):
    """
    Carica un file .asc e restituisce:
    - array 2D (numpy)
    - metadata
    """

    with open(filepath, "r") as f:
        header = {}
        for _ in range(6):
            line = f.readline().strip().split()
            header[line[0].lower()] = float(line[1])

        data = np.loadtxt(f)

    return data, header


# ======================================================
# COORDINATE → INDEX
# ======================================================

def latlon_to_rowcol(lat, lon, header):
    """
    Converte lat/lon → indici raster
    """

    xll = header["xllcorner"]
    yll = header["yllcorner"]
    cellsize = header["cellsize"]
    nrows = int(header["nrows"])

    col = int((lon - xll) / cellsize)
    row_from_bottom = int((lat - yll) / cellsize)

    # raster è top-down → inverti riga
    row = nrows - 1 - row_from_bottom

    return row, col


# ======================================================
# VALUE EXTRACTION
# ======================================================

def get_value_from_asc(lat, lon, data, header):
    """
    Restituisce valore raster per una coordinata
    """

    row, col = latlon_to_rowcol(lat, lon, header)

    if (
        row < 0 or col < 0 or
        row >= data.shape[0] or
        col >= data.shape[1]
    ):
        return None

    value = data[row, col]

    if value == header.get("nodata_value", -9999):
        return None

    return float(value)


# ======================================================
# VECTOR EXTRACTION (CSV → raster)
# ======================================================

def extract_values_for_dataframe(df, data, header,
                                 lat_col="Latitude",
                                 lon_col="Longitude"):
    """
    Estrae valori raster per tutte le righe del dataframe
    """

    values = []

    for _, row in df.iterrows():
        lat = row[lat_col]
        lon = row[lon_col]

        val = get_value_from_asc(lat, lon, data, header)
        values.append(val)

    return np.array(values)