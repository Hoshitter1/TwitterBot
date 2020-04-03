FROM python:3.7.2

#TODO Not sure which dir is the best for this project yet
ENV APP_PATH /opt/apps

# Set up token and secret for twitter
ARG ACCESS_TOKEN
ENV ACCESS_TOKEN=$ACCESS_TOKEN
ARG ACCESS_TOKEN_SECRET
ENV ACCESS_TOKEN_SECRET=$ACCESS_TOKEN_SECRET
ARG CONSUMER_KEY
ENV CONSUMER_KEY=$CONSUMER_KEY
ARG CONSUMER_SECRET
ENV CONSUMER_SECRET=$CONSUMER_SECRET

#　Slack
ARG SLACK_TOKEN
ENV SLACK_TOKEN=$SLACK_TOKEN

COPY . $APP_PATH/
RUN pip install --no-cache-dir -r $APP_PATH/requirements.txt
#For postgre
RUN pip install psycopg2
#For debugging
RUN apt update && apt install -y vim

WORKDIR $APP_PATH
