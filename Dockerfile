FROM apache/airflow:2.9.1

USER root

# Force reinstall kafka-python and six system-wide to avoid vendor import issues
RUN pip install --force-reinstall --no-cache-dir kafka-python==1.4.7 six==1.17.0

# Optional: project requirements
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt || true

USER airflow
