# Evaluador Automatico NIST e ISO 27001

Prototipo funcional para materializar el evaluador automatico de ciberseguridad para PYMES definido en la tesis. La evaluacion se basa en los criterios seleccionados del Apendice A: NIST CSF 2.0 e ISO/IEC 27001.

## Funciones incluidas

- Inicio de sesion.
- Registro de empresas evaluadas.
- Perfil de empresa con sector, cantidad de empleados y auditor responsable.
- Dashboard con total de evaluaciones, alineacion NIST, cumplimiento interno ISO, brechas criticas y criterios sin evidencia.
- Creacion de evaluaciones por empresa, fecha y auditor.
- Seleccion del marco evaluado: NIST CSF 2.0, ISO/IEC 27001 o ambos.
- Catalogo persistente de criterios en SQLite, sembrado desde las matrices del Apendice A.
- Cuestionario con 35 criterios:
  - NIST CSF 2.0: N-01 a N-12, organizado en Govern, Identify, Protect, Detect, Respond y Recover.
  - ISO/IEC 27001: I-01 a I-23, organizado por las areas definidas en la matriz de la tesis.
- Registro de evidencias mediante observaciones y archivos adjuntos.
- Calculo automatico con valores: cumple 100, cumple parcialmente 50, no cumple 0 y no aplica excluido del calculo.
- Calculo separado de alineacion NIST y cumplimiento interno ISO. Si se seleccionan ambos referentes, se evalua en una misma evaluacion, pero los resultados se mantienen separados.
- Indicadores de brechas criticas, controles cumplidos y controles pendientes.
- Distribucion de respuestas y principales oportunidades de mejora.
- Reporte PDF con resumen, evidencias, brechas y recomendaciones.

## Credenciales demo

- Usuario: `admin`
- Contrasena: `admin123`
- Usuario de consulta: `profesor`
- Contrasena: `tesis2026`
- Usuario empresa: `empresa`
- Contrasena: `empresa2026`

## Permisos

- Auditor: puede registrar empresas, crear evaluaciones, adjuntar evidencias, consultar dashboard y generar reportes.
- Empresa: puede responder evaluaciones y cargar evidencias.
- Revisor: puede consultar dashboard, resultados y reportes. No puede registrar empresas, crear evaluaciones ni subir evidencias.

## Ejecutar el proyecto con Docker

Esta es la forma recomendada para que otra persona pueda correr el sistema sin instalar Python, Node.js ni dependencias manualmente.

### Requisitos

La otra persona debe tener instalado:

- Git: https://git-scm.com/downloads
- Docker Desktop: https://www.docker.com/products/docker-desktop/

Antes de ejecutar los comandos, Docker Desktop debe estar abierto.

### Pasos

1. Abrir una terminal.

2. Descargar el repositorio:

```powershell
git clone https://github.com/Reidy07/TESIS.git
```

3. Entrar a la carpeta del proyecto:

```powershell
cd TESIS
```

4. Construir la imagen de Docker:

```powershell
docker build -t evaluador-nist-iso .
```

5. Ejecutar la aplicacion:

```powershell
docker run -p 10000:10000 evaluador-nist-iso
```

6. Abrir la aplicacion en el navegador:

```text
http://localhost:10000
```

### Usuarios de prueba

```text
Auditor:
usuario: admin
contrasena: admin123

Revisor:
usuario: profesor
contrasena: tesis2026

Empresa:
usuario: empresa
contrasena: empresa2026
```

### Si el puerto esta ocupado

Si `10000` ya esta siendo usado, se puede correr con otro puerto local. Por ejemplo:

```powershell
docker run -p 8080:10000 evaluador-nist-iso
```

Y luego abrir:

```text
http://localhost:8080
```

## Ejecutar backend

```powershell
cd backend
python app.py
```

API disponible en:

```text
http://127.0.0.1:5000
```

## Ejecutar frontend

```powershell
cd frontend
npm install
npm run dev -- --port 5173
```

Aplicacion disponible en:

```text
http://127.0.0.1:5173
```
