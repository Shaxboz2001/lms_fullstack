FROM jupyter/pyspark-notebook

# Root bo‘lib ishlash
USER root

# Hadoop AWS va AWS SDK kerak S3 uchun
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.2/hadoop-aws-3.3.2.jar -P /usr/local/spark/jars/ && \
    wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar -P /usr/local/spark/jars/

# Keyin yana jovyan foydalanuvchiga qaytamiz (jupyter default user)
USER $NB_UID

# Default sozlamalar
ENV PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=jupyter \
    PYSPARK_DRIVER_PYTHON_OPTS="lab --ip=0.0.0.0 --no-browser --allow-root"
