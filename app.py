# PostulaPro Web App (con Streamlit)
# Interfaz web para generar propuestas de licitación en Chile

import streamlit as st
from datetime import date

# Simulación del agente PostulaPro mejorado con bases reales (ID 2239-8-LR25)
def generar_propuesta(razon_social, experiencia, capacidades, precios, documentos, bases):
    resumen = f"Propuesta para la licitación pública Convenio Marco ID 2239-8-LR25 para artículos de aseo e higiene, presentada por {razon_social}."
    tecnica = (
        f"Nuestra empresa, {razon_social}, cuenta con {experiencia}."
        f" Nos especializamos en {capacidades}, cumpliendo con los requisitos exigidos en las bases, como inscripción vigente en el Registro de Proveedores,"
        f" declaración jurada, uso de productos con registro INAPI/ISP, y condiciones técnicas y logísticas conforme a las normativas de ChileCompra."
    )
    economica = "\n".join([f"{item}: ${precio}" for item, precio in precios.items()])
    carta = (
        f"Sres. Comisión Evaluadora,\n\n"
        f"Por medio de la presente, {razon_social} presenta su postulación a la licitación pública ID 2239-8-LR25 para el Convenio Marco de Artículos de Aseo e Higiene,"
        f" de acuerdo a lo establecido en las Bases Administrativas y Técnicas aprobadas por Resolución Exenta."
        f" Nos comprometemos a cumplir con los estándares técnicos, normativos y contractuales exigidos."
    )
    checklist = [
        'Bases leídas',
        'Oferta técnica redactada',
        'Oferta económica generada',
        'Documentos legales adjuntos (Registro de Proveedores, Certificados)',
        'Carta de presentación firmada',
        'Declaraciones juradas completadas en plataforma',
        'Revisión de INAPI/ISP para productos ofertados'
    ]
    analisis = (
        "La oferta técnica fue desarrollada en base a los criterios establecidos en las bases del Convenio Marco,"
        " priorizando cumplimiento normativo, experiencia comprobable, condiciones logísticas a nivel nacional y registro de productos."
        " La estrategia económica se enfoca en mantener precios competitivos dentro del rango evaluable según metodología boxplot usada por la DCCP."
    )

    return {
        'Resumen Ejecutivo': resumen,
        'Oferta Técnica': tecnica,
        'Oferta Económica': economica,
        'Carta de Presentación': carta,
        'Checklist': checklist,
        'Análisis Estratégico': analisis,
        'Documentos Adjuntos': documentos
    }

# Interfaz Streamlit
st.title("PostulaPro: Generador de Propuestas para Mercado Público")

with st.form("formulario_propuesta"):
    st.header("Datos del Proveedor")
    razon_social = st.text_input("Razón Social")
    experiencia = st.text_area("Experiencia Previa")
    capacidades = st.text_area("Capacidades Técnicas")

    st.header("Precios Ofertados")
    precios_input = st.text_area("Escriba los ítems y precios (ej: 'Producto A: 10000')")
    precios = dict()
    for linea in precios_input.splitlines():
        if ":" in linea:
            item, precio = linea.split(":")
            precios[item.strip()] = precio.strip()

    st.header("Documentación Legal")
    documentos = st.text_area("Lista de documentos adjuntos (uno por línea)").splitlines()

    st.header("Bases de Licitación")
    bases = st.text_area("Resumen o texto de bases de licitación")

    submitted = st.form_submit_button("Generar Propuesta")

if submitted:
    propuesta = generar_propuesta(razon_social, experiencia, capacidades, precios, documentos, bases)
    st.success("¡Propuesta Generada!")
    for seccion, contenido in propuesta.items():
        st.subheader(seccion)
        if isinstance(content, list):
            for item in content:
                st.markdown(f"- {item}")
        else:
            st.text_area(label=seccion, value=contenido, height=150)
