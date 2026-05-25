# Gatling Performance Test Prototype

This folder contains a Gatling load testing prototype 
for the Patient Experience appointment history flow.

## Endpoint Tested

`GET http://127.0.0.1:5000/api/appointment-history`

This endpoint is used by the frontend `AppointmentHistory.jsx` page 
through the `getAllAppointmentHistory()` API helper.

## Purpose

The goal of this prototype is to use Gatling, a load testing tool, to the Simple Medical Appointments
project by measuring how the appointment history endpoint responds under light simulated user load.

## Report Output

Gatling generates an HTML report under:
gatling/target/gatling/appointmenthistory-timestamp

open the index.html file to see results from running.

## Running the Test

Start the Flask backend first:

```bash
cd backend
venv\Scripts\activate
python run.py
```

in another cmd, run gatling from the gatling directory in backend/tests/performance/gatling

```bash
cd backend/tests/performance/gatling
mvnw.cmd gatling:test
```

This installs gatling and runs test. 
`gatling/src/test/java/simplemedicalappointments/` is used because this 
Gatling prototype is a Maven-based Java test project. 
The `mvnw.cmd gatling:test` command uses pom.xml to install the required Gatling dependencies,
then finds and runs the Java simulation stored under the standard src/test/java test path.


