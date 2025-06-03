# PostulaPro Web

Generador automático de propuestas de postulación para licitaciones públicas en Chile, con foco en el **Convenio Marco de Aseo e Higiene (ID 2239-8-LR25)**.

---

## 🧠 Características

* Verificación de proveedor por RUT contra padrón oficial
* Generación automática de:

  * Carta de presentación
  * Oferta técnica
  * Oferta económica
  * Análisis estratégico
  * Checklist de cumplimiento
* Exportación a Word con anexo numerado
* Validaciones de campos y precios
* Envió de propuesta por correo electrónico
* Recordatorio automático de fechas clave

---

## 📅 Fechas importantes

> 🔔 Cierre postulaciones: **viernes 7 de junio de 2025 a las 15:00 hrs**

---

## 🚀 Cómo usar

```bash
# 1. Clona el repo
git clone https://github.com/evarasvb/postulapro-web.git
cd postulapro-web

# 2. Instala dependencias
pip install -r requirements.txt

# 3. Ejecuta la app
streamlit run app.py
```

---

## 📂 Archivos clave

| Archivo                                     | Descripción                                   |
| ------------------------------------------- | --------------------------------------------- |
| `app.py`                                    | Aplicación principal con Streamlit            |
| `requirements.txt`                          | Dependencias (streamlit, pandas, python-docx) |
| `README.md`                                 | Esta documentación                            |
| `ListadoProveedoresVigentes-02-06-2025.pdf` | Archivo para validación de RUT                |

---

## 🚫 Limitaciones

* No envía ofertas automáticas a Mercado Público
* No valida los productos por ficha técnica (en desarrollo)

---

## 📄 Captura de pantalla

> *(Puedes subir una imagen de tu app funcionando en Streamlit y colocar aquí un enlace o markdown)*

---

## 🌟 Créditos

Hecho con ❤️ por [evarasvb](https://github.com/evarasvb)

---

## 📢 Licencia

MIT License

---

