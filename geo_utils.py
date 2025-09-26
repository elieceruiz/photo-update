# ---------------------------
# Funciones de conversión de coordenadas
# ---------------------------

def decimal_a_gms(decimal_coord):
    """
    Convierte coordenadas decimales a grados, minutos y segundos (GMS)
    """
    grados = int(decimal_coord)
    decimales = abs(decimal
