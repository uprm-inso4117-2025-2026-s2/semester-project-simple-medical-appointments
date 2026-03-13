export default function SlotUsageSummary({ doctorId, selectedDate }) {
  
    /*
      Future Query Logic:
  
      SELECT appointment_type, COUNT(*)
      FROM appointment
      WHERE doctor_id = doctorId
        AND appointment_date = selectedDate
      GROUP BY appointment_type;
  
      Map results to:
      - MAIN
      - WAITLIST
      - OVERRIDE
    */
  
    const mainCount = 5;
    const waitlistCount = 3;
    const overrideCount = 1;
  
    return (
      <div>
        <h3>Slot Usage Summary</h3>
        <p>Main: {mainCount}</p>
        <p>Waitlist: {waitlistCount}</p>
        <p>Override: {overrideCount}</p>
      </div>
    );
  }