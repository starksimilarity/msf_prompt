FROM python:3.8

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

WORKDIR /usr/src/app/msf_prompt
CMD ["python", "msf_prompt.py"]
