# Official Python 3.13.5 slim-bookworm manifest, inspected on 2026-10-11.
FROM python:3.13.5-slim-bookworm@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419
COPY requirements.txt /opt/vericode/requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r /opt/vericode/requirements.txt
COPY runner.py pytest.ini /opt/vericode/
RUN chmod -R a-w /opt/vericode && mkdir /workspace && chmod 0700 /workspace
LABEL io.vericode.runner="2"
USER 65532:65532
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/python", "-I", "-B", "/opt/vericode/runner.py"]
