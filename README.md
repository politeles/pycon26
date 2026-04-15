# PyCon 2026 talks: Arquitectura de sistemas multiagente: gestionando memoria, gestionando comunicaciones

En este repo mostramos código de ejemplo para las charlas de PyCon 2026 sobre arquitectura de sistemas multiagente, gestión de memoria y gestión de comunicaciones.

Para ilustrar el funcionamiento de un agente básico, hemos preparado un notebook de Jupyter con un ejemplo implementado con la librería SmolAgents. En este ejemplo, comenzamos usando una LLM base para luego crear un agente básico con SmolAgents y mejorarlo para podamos obtener una respuesta adecuada. El notebook se encuentra en `PyCon26_Intro_smolagents.ipynb`.

El código está organizado en carpetas según el tema:

La carpeta `Comms/A2A` contiene un ejemplo de sistema multiagente con comunicación A2A (agent-to-agent) vía HTTP. En este ejemplo, un agente generalista de búsqueda web delega consultas sobre conferencias PYCON a un agente especializado usando el protocolo A2A.

Para ejecutar estos ejemplos, es necesario configurar el token de Hugging Face en un archivo `.env` con la variable `HF_TOKEN`.

Hemos configurado las dependencias usando poetry, por lo que para instalar las dependencias basta con ejecutar `poetry install` en la raíz del proyecto.

Finalmente, para ejecutar el sistema multiagente de la carpeta `Comms/A2A`, primero hay que iniciar el agente especializado con `poetry run python Comms/A2A/py_agent.py` y luego el agente generalista con `poetry run python Comms/A2A/agent_orchestrator.py`. El agente generalista escuchará por consultas, y si detecta que la consulta es sobre conferencias PYCON, delegará la consulta al agente especializado vía A2A.
