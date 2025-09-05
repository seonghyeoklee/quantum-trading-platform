# Airflow Custom Image for Quantum Trading Platform
FROM apache/airflow:2.8.2

# Switch to airflow user
USER airflow

# Copy and install Python requirements
COPY --chown=airflow:root requirements.txt /requirements.txt
RUN pip install --user --no-cache-dir -r /requirements.txt