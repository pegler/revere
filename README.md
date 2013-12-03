Revere [![Build Status](https://travis-ci.org/pegler/revere.png)](https://travis-ci.org/pegler/revere) [![Coverage Status](https://coveralls.io/repos/pegler/revere/badge.png)](https://coveralls.io/r/pegler/revere)
=========

Disclaimer
-----

Revere runs Python entered via a webpage.  It currently makes no attempt to sandbox this code.  Always run Revere as a non-privledged user and ensure it is secured behind some sort of authentication.

This project was inspired by [LivingSocial's Rearview](https://github.com/livingsocial/rearview).  We have been using it without issue for serveral weeks, but it is far from stable.

There is no built in authentication.  You must secure Revere behind your firewall somehow.

Terms
-----

 - *source* - a source of data.  A database, graphite server, or 3rd party monitoring API
 - *alert* - a way of alerting you when certain criteria are met.  Campfire, AWS SNS, email, text, etc.
 - *monitor* - a script that runs on a schedule and pulls data from one or more sources.  A monitor can indicate it is in an Alarm state, in which case the alerts will be fired.

Features
-----

 - Pluggable sources of data
 - Pluggable alerts to notify you
 - Write your moniors using Python and specify the schedule using crontab syntax
 - Store the return value of the monitor (numbers or strings) for each run
 - Automatic purging of old data (day granularity)

Revere is a general purpose monitoring and alerting system.  It has pluggable sources of data and alerts.  So you can pull data from anywhere you want and then trigger alarms when certain thresholds are crossed.

Installation
------

```
pip install git+git://github.com/pegler/revere.git

//create a config file.  defaults will be used if missing from the file
touch config.py

//create the SQLite database
revereserver.py init

//run Revere. defaults to port 5000
revereserver.py run
```


Configuration
------

Revere uses a python file named config.py in the current working directory.  The configuration variables are:

 - `DATABASE_PATH` - the path to the SQLite file
 - `REVERE_SOURCES` - a dict specifying the sources.  The key can be anything and is used by the monitors to access the source.  The value is a configuration dict for the source.
 - `REVERE_ALERTS` - a dict specifying the alerts

Example config.py file:

```
DATABASE_PATH = 'revere.db'

REVERE_SOURCES = {
    'graphite': {
        'description': 'Graphite Server',
        'type': 'revere.sources.graphite.GraphiteSource',
        'config': {
            'url': 'http://dashing.example.com/render',
            'auth_username': 'username',
            'auth_password': 'password',
        }
    },
    'mysql': {
        'description': 'Local MySQL Database',
        'type': 'revere.sources.database.DatabaseSource',
        'config': {
            'connection_string': 'mysql://readonlyuser:password@localhost/production',
        }
    }
}

REVERE_ALERTS = {
    'campfire-engineering': {
        'description': 'Post a message to Campfire - Engineering',
        'type': 'revere.alerts.campfire.CampfireAlert',
        'config': {
            'api_token': 'xxxxxx',
            'subdomain': 'example',
            'room_id': '123456',
        }
    },
    'teamup-ops-sns': {
        'description': 'Publish a message to AWS SNS Topic operations',
        'type': 'revere.alerts.sns.SNSAlert',
        'config': {
            'region': 'us-east-1',
            'topic_arn': 'xxxxx',
            'access_key_id': 'xxxxx',
            'secret_key': 'xxxxx',
        }
    }
}
```

Monitors
-----

Monitors are configured using simple Python.  Simply navigate to the "Create Monitor" page, specify the schedule using crontab syntax, specify the retention period, and then write the Python that does the checking.  The script is executed with a dictionary named `sources` in scope that has the various sources configured available.  The keys are the same as specified in the configuration file.

If the monitor has "failed" and should be in the ALARM state, the code should raise a `MonitorFailure` exception.  The message passed into the exception will be included in any alerts triggered from the ALARM state.

Any other exception raised will be change the monitor to the ERROR state and trigger any enabled alerts.

Any data assigned to the variable `return_value` will be recorded.  The data must be an int, float, long, string, or unicode.

An example monitor:

```
total_requests = sources['dashing'].get_sum('sum(stats_counts.response.*)','-10min')
error_requests = sources['dashing'].get_sum('stats_counts.response.500','-10min')
error_percentage = error_requests/total_requests
return_value = error_percentage

if error_percentage >= .005:
    raise MonitorFailure('High number of error responses. %s%%' % (error_percentage))
```

Alerts will often include the return value, message passed into `MonitorFailure`, and the current state of the monitor.


Sources
------

### revere.sources.graphite.GraphiteSource

Pull data from a Graphite server.

#### Configuration

Parameters:

 - *url* - the url of the graphite server
 - *auth_username* (optional) - username for basic authentication
 - *auth_password* (optional) - password for basic authentication

#### Usage

It has 3 methods, all with identical parameters.

 - `path` - the dotted path for the data to retreive.  Graphite functions can be passed in.
 - `from_date` - any valid graphite starting time.  example: '-5d'
 - `to_date` - any valid graphite starting time.  example: '-2d'

Methods:

 - `get_datapoints(path, from_date=None, to_date=None)` - return a list of `(value, timestamp)` pairs for the path within the given timeframe
 - `get_sum(path, from_date=None, to_date=None)` - return the sum of the values.  null values are counted as 0
 - `get_avg(path, from_date=None, to_date=None)` - return the average of the values.  null values are counted as 0

### revere.sources.database.DatabaseSource

Connect to any database.  It uses SQLAlchemy for connections, which supports most databases.

#### Configuration

Parameters:

 - *connection_string* - the SQLAlchemy connection string to the database.  See: http://pythonhosted.org/Flask-SQLAlchemy/config.html#connection-uri-format
 - *pool_recycle* (default: 3600) - number of seconds before a connection in the pool should be recycled

#### Usage

The only method is `execute(sql, as_dict=False)` which accepts raw SQL and returns either a list of tuples.  If `as_dict` is `True`, it will return a list of dicts keyed on the column names.

Alerts
-----

Alerts can be configured to only fire when a monitor transitions to a particular state.  So you can get a phone call when a monitor is in the ALARM state, but only get an email when it goes back to the OK state.

### revere.alerts.campfire.CampfireAlert

Send a message to a Campfire room of the form:

```
[Revere Alarm]
Monitor: Mail Queue Length
State Change: ALARM -> OK
Message: Monitor Passed
Return Value: 67
```

#### Configuration

 - *api_token* - the API token for the user to send the message as
 - *room_id* - the id for the room to post to.  Find this in the URL of the room
 - *subdomain* - the subdomain for the room to post to.  Find this in the URL of the room


### revere.alerts.sns.SNSAlert

Send a message to an Amazon Web Services' Simple Notification Service (AWS SNS) Topic.  It will include a subject and body for emails as well as a shortened message to be sent to SMS subscribers.


#### Configuration

 - *topic_arn* - the topic ARN to post to.  Of the form: `arn:aws:sns:us-east-1:1234567890:topic-name`
 - *access_key_id* - the API Access Key ID to post to the topic
 - *secret_key* - the API Secret Key to post to the topic


Screenshots
-----

A list of monitors with their current state and time since last run
![image](https://f.cloud.github.com/assets/94491/1660360/feda76dc-5bba-11e3-8ce4-fc3afe39afe4.png)

---

The overview page for a monitor.  It lists the past state changes including the return value from the monitor and alarm message.
![image](https://f.cloud.github.com/assets/94491/1660395/b2274076-5bbb-11e3-9409-71ee87cb7ccc.png)

---

Full history for a monitor
![image](https://f.cloud.github.com/assets/94491/1660415/1a60336e-5bbc-11e3-8b1b-d195f146b361.png)

---

The list of alerts and which states they get triggered for.
![image](https://f.cloud.github.com/assets/94491/1660354/d1abe894-5bba-11e3-8bae-ad89a77d288c.png)


Thanks
------

This project is mostly just cobbling together several other excellent projects.

 - [Flask](http://flask.pocoo.org/) - the web front-end
 - [SQLAlchemy](http://www.sqlalchemy.org/) - excellent lightweight database wrapper
 - [APScheduler](http://pythonhosted.org/APScheduler/) - managing the schedule for the monitors
 - [Tornado](http://www.tornadoweb.org/en/stable/) - lightweight web server
