FROM astrocrpublic.azurecr.io/runtime:3.1-3

# Install Microsoft ODBC Driver 17 for SQL Server
USER root

# Install prerequisites
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https

# Add Microsoft repository and install ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER astro
