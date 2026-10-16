FROM python:3.12-slim AS build
WORKDIR /src
COPY app.py /src/app.py
RUN dd if=/dev/urandom of=/src/junk.bin bs=1048576 count=20

FROM python:3.12-slim
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build /src/app.py /app/app.py
USER app
EXPOSE 8000
CMD ["python", "app.py"]
