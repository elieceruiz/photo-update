# geo_utils.py
def decimal_a_gms(decimal_coord):
    grados = int(decimal_coord)
    decimales = abs(decimal_coord - grados)
    minutos_dec = decimales * 60
    minutos = int(minutos_dec)
    segundos = (minutos_dec - minutos) * 60
    return grados, minutos, segundos

def formato_gms(grados, minutos, segundos):
    # Formatea en string: 6° 18' 56.35"
    return f"{grados}° {minutos}' {segundos:.2f}\""
