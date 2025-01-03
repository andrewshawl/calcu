import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------------------------------
# CONSTANTES GLOBALES
# -------------------------------------------------------------------------
LOTES_A_UNIDADES = 100  # 1 lote = 100 unidades
PASO = 15  # Paso de precio ajustado a 15 unidades
TOTAL_UNIDADES = 120  # Total de unidades a cubrir
DIVISOR_LOTE = 1.5932  # Divisor para ajustar los lotajes
DIVISOR_CONSERVADOR = 2.11 # Divisor adicional para la opción conservadora
DIVISOR_MUY_AGRESIVA = 1.6 # Divisor para la opción muy agresiva
DIVISOR_SEMI_AGRESIVA = 2.25 # Divisor para la opción semi agresiva

# -------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------------

def generar_precios(precio_inicial, total_unidades, paso=15, direccion="bajada"):
    """
    Genera una lista de precios decrecientes o crecientes desde precio_inicial dependiendo de la dirección.
    """
    numero_puntos = total_unidades // paso + 1  # +1 para incluir el precio final
    if direccion == "bajada":
        precios = [precio_inicial - i * paso for i in range(numero_puntos)]
    elif direccion == "subida":
        precios = [precio_inicial + i * paso for i in range(numero_puntos)]
    else:
        raise ValueError("La dirección debe ser 'bajada' o 'subida'.")
    return precios

def asignar_lotes(precio_inicial, precios, opcion):
    """
    Asigna lotes basados en la diferencia de precio desde el precio inicial.
    """
    lotes = []
    for i, precio in enumerate(precios):
        if i == 0:  # Para el precio inicial
            lotes.append(1.0)
        elif i == 1:  # Para la segunda compra
            lotes.append(1.4)
        elif i == 2:  # Para la tercera compra
            lotes.append(2.4)
        elif i == 3:  # Para la cuarta compra
            lotes.append(2)
        elif i == 4:  # Para la quinta compra
            lotes.append(2.4 * 1.3)
        elif i == 5:  # Para la sexta compra
            if opcion == 1:
                lotes.append(0)
            elif opcion in [2, 3, 4, 5, 6]:
                lotes.append(2.4 * 1.3)
            elif opcion == 7:  # Semi Conservadora
                lotes.append(2)  # Mismo lotaje que la compra 4 indexada por 3
        elif i == 6:
            lotes.append(3 * 1.5)
        elif i == 7:  # Para la octava compra
            if opcion == 1 or opcion == 7:  # Neutra o Semi Conservadora
                lotes.append(0)
            elif opcion == 2:
                lotes.append(3)
            elif opcion in [3, 4, 5, 6]:
                lotes.append(3)
        elif i == 8:
            lotes.append(4 * 1.5)
        else:
            diferencia = abs(precio_inicial - precio)
            if 0 <= diferencia <= 15:
                lotes.append(0.5)
            elif diferencia == 20:
                lotes.append(0.0)
            elif diferencia in [25, 30]:
                lotes.append(2.0)
            elif 35 <= diferencia <= 55:
                if diferencia == 55:
                    lotes.append(0.0)
                else:
                    lotes.append(0.625)
            elif diferencia == 60:
                lotes.append(6.0)
            elif 65 <= diferencia <= 90:
                lotes.append(2.0)
            elif 91 <= diferencia <= 94:
                lotes.append(1.5)
            elif 95 <= diferencia <= 120:
                lotes.append(3.375)
            else:
                lotes.append(0.5)

    # Dividir los lotajes según la opción seleccionada
    if opcion == 3:
        lotes_ajustados = [lote / DIVISOR_CONSERVADOR for lote in lotes]
    elif opcion == 4:  # Muy Agresiva
        lotes_ajustados = [(lote * 1.25) / DIVISOR_MUY_AGRESIVA for lote in lotes]
    elif opcion == 5:  # Semi Agresiva
        lotes_ajustados = [(lote * 1.25) / DIVISOR_SEMI_AGRESIVA for lote in lotes]
    elif opcion == 6:  # Súper Agresiva
        lotes_ajustados = [(lote * 1.25 * 1.2) / DIVISOR_MUY_AGRESIVA for lote in lotes]
    else:
        lotes_ajustados = [lote / DIVISOR_LOTE for lote in lotes]

    return lotes_ajustados

def crear_dataframe(precios, lotes):
    """
    Crea un DataFrame con los precios y los lotes asignados.
    """
    df = pd.DataFrame({
        'Precio': precios,
        'Lotes': lotes
    })
    return df

def calcular_acumulados(df, precio_inicial, direccion):
    """
    Calcula los lotes acumulados, break-even, flotante, puntos de salida.
    También calcula el aumento necesario desde el precio actual para ganar $5000.
    """
    df['Lotes Acumulados'] = df['Lotes'].cumsum()
    df['Break Even'] = (df['Precio'] * df['Lotes'] * LOTES_A_UNIDADES).cumsum() / (df['Lotes Acumulados'] * LOTES_A_UNIDADES)
    df['Flotante'] = (df['Precio'] - df['Break Even']) * df['Lotes Acumulados'] * LOTES_A_UNIDADES
    # Calcular puntos de salida con signo dependiendo de la dirección
    if direccion == "subida":
        df['Puntos de salida'] = df['Break Even'] - df['Precio']
    else:
        df['Puntos de salida'] = abs(df['Precio'] - df['Break Even'])
    # Calcular el aumento necesario desde el precio actual para ganar $5000
    df['Aumento Necesario para $5000'] = (df['Break Even'] + (5000 / (df['Lotes Acumulados'] * LOTES_A_UNIDADES))) - df['Precio']
    # Calcular ganancia si el precio regresa al inicial
    if direccion == "subida":
        df['Ganancia al Regresar al Precio Inicial'] = (df['Precio'] - precio_inicial) * df['Lotes Acumulados'] * LOTES_A_UNIDADES * -1
    else:
        df['Ganancia al Regresar al Precio Inicial'] = (precio_inicial - df['Precio']) * df['Lotes Acumulados'] * LOTES_A_UNIDADES
    # Reemplazar inf, -inf y NaN en caso de divisiones por cero o acumulación cero
    df['Aumento Necesario para $5000'] = df['Aumento Necesario para $5000'].replace([np.inf, -np.inf, np.nan], 0)
    df['Ganancia al Regresar al Precio Inicial'] = df['Ganancia al Regresar al Precio Inicial'].replace([np.inf, -np.inf, np.nan], 0)
    return df

def validar_precio_final(df, precio_esperado):
    """
    Verifica que el último precio en el DataFrame sea igual al precio esperado.
    """
    ultimo_precio_calculado = df['Precio'].iloc[-1]
    if ultimo_precio_calculado != precio_esperado:
        st.error(f"Error: El último precio calculado es {ultimo_precio_calculado}, pero se esperaba {precio_esperado}.")
        return False
    return True

# -------------------------------------------------------------------------
# APLICACIÓN PRINCIPAL DE STREAMLIT
# -------------------------------------------------------------------------

def main():
    st.title("Calculadora de Distribución en Tramos (Intervalos de 15)")

    # Entrada del usuario: Precio inicial
    precio_inicial = st.number_input(
        "Precio inicial del oro (p):",
        min_value=1.00,
        value=2700.00,
        step=15.00,
        format="%.2f"
    )

    # Entrada del usuario: Dirección (subida o bajada)
    direccion = st.selectbox("Seleccione la dirección:", ["bajada", "subida"])

    # Entrada del usuario: Opción para asignar lotes
    opcion = st.selectbox("Seleccione la opción de asignación de lotes:", ["Conservadora", "Semi Conservadora", "Neutra", "Semi Agresiva", "Agresiva", "Muy Agresiva", "Súper Agresiva"], index=0)
    opcion_numerica = {"Conservadora": 3, "Semi Conservadora": 7, "Neutra": 1, "Semi Agresiva": 5, "Agresiva": 2, "Muy Agresiva": 4, "Súper Agresiva": 6}[opcion]

    # Botón para ejecutar el cálculo
    if st.button("Calcular Distribución en Tramos"):
        # Generar lista de precios
        precios = generar_precios(precio_inicial, TOTAL_UNIDADES, PASO, direccion)

        # Asignar lotes según las reglas y ajustar
        lotes = asignar_lotes(precio_inicial, precios, opcion_numerica)

        # Verificar que las listas tengan la misma longitud
        if len(precios) != len(lotes):
            st.error("Error: Las listas de precios y lotes no tienen la misma longitud.")
        else:
            # Crear DataFrame
            df = crear_dataframe(precios, lotes)

            # Calcular acumulados
            df = calcular_acumulados(df, precio_inicial, direccion)

            # Redondear valores para mejor visualización
            df['Precio'] = df['Precio'].round(2)
            df['Lotes'] = df['Lotes'].round(4)
            df['Lotes Acumulados'] = df['Lotes Acumulados'].round(4)
            df['Break Even'] = df['Break Even'].round(2)
            df['Flotante'] = df['Flotante'].round(2)
            df['Puntos de salida'] = df['Puntos de salida'].round(2)
            df['Aumento Necesario para $5000'] = df['Aumento Necesario para $5000'].round(2)
            df['Ganancia al Regresar al Precio Inicial'] = df['Ganancia al Regresar al Precio Inicial'].round(2)

            # Calcular precio esperado
            precio_esperado = precio_inicial + TOTAL_UNIDADES if direccion == "subida" else precio_inicial - TOTAL_UNIDADES

            # Validar el precio final
            es_valido = validar_precio_final(df, precio_esperado)

            if es_valido:
                # Mostrar resultados
                st.write("### Detalles de las Transacciones:")
                st.dataframe(df)

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
