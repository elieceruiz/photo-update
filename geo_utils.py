# geo_utils.py
def decimal_a_gms(decimal_coord):
    grados = int(decimal_coord)
    decimales = abs(decimal_coord - grados)
    minutos_dec = decimales * 60
    minutos = int(minutos_dec)
    segundos = (minutos_dec - minutos) * 60
    return grados, minutos, segundos

def hemisferio_latitud(lat):
    return 'N' if lat >= 0 else 'S'

def hemisferio_longitud(lon):
    return 'E' if lon >= 0 else 'W'

def formato_gms_con_hemisferio(lat, lon):
    lat_g, lat_m, lat_s = decimal_a_gms(lat)
    lon_g, lon_m, lon_s = decimal_a_gms(lon)
    lat_h = hemisferio_latitud(lat)
    lon_h = hemisferio_longitud(lon)
    lat_str = f"{abs(lat_g)}° {lat_m}' {lat_s:.2f}\" {lat_h}"
    lon_str = f"{abs(lon_g)}° {lon_m}' {lon_s:.2f}\" {lon_h}"
    return lat_str, lon_str
