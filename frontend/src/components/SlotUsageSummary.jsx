export default function SlotUsageSummary({ doctorId, selectedDate }) {

  /*
    Future Query Logic:

    SELECT appointment_type, COUNT(*)
    FROM appointment
    WHERE doctor_id = doctorId
      AND appointment_date = selectedDate
    GROUP BY appointment_type;
  */

  const mainCount = 0;
  const waitlistCount = 0;
  const overrideCount = 0;

  return (
    <div>
      <h3>Slot Usage Summary</h3>
      <p>Main: {mainCount}</p>
      <p>Waitlist: {waitlistCount}</p>
      <p>Override: {overrideCount}</p>
    </div>
  );
}