package simplemedicalappointments;

import io.gatling.javaapi.core.ScenarioBuilder;
import io.gatling.javaapi.core.Simulation;
import io.gatling.javaapi.http.HttpProtocolBuilder;

import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;

public class AppointmentHistorySimulation extends Simulation {

    private final HttpProtocolBuilder httpProtocol = http
        .baseUrl("http://127.0.0.1:5000")
        .acceptHeader("application/json")
        .contentTypeHeader("application/json");

    private final ScenarioBuilder scenario = scenario("Patient Appointment History Load Test")
        .exec(
            http("GET /api/appointment-history")
                .get("/api/appointment-history")
                .check(status().is(200))
        );

    {
        // setUp(
        //     scenario.injectOpen(
        //         atOnceUsers(1),
        //         rampUsers(10).during(30)
        //     )
        
    setUp(
        scenario.injectOpen(
            atOnceUsers(1),
            rampUsers(10).during(30),
            constantUsersPerSec(2).during(60)
        )
    ).protocols(httpProtocol);


    }
}