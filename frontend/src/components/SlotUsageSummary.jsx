const placeholderSections = [
  {
    title: 'Main slot usage',
    value: '0 of 0 slots used',
    note: 'Temporary placeholder for the primary appointment queue.',
  },
  {
    title: 'Waitlist slot usage',
    value: '0 waitlist entries',
    note: 'Temporary placeholder for patients waiting on availability.',
  },
  {
    title: 'Override slot usage',
    value: '0 override bookings',
    note: 'Temporary placeholder for manually approved slot overrides.',
  },
  {
    title: 'Utilization percentages',
    value: '0% utilized',
    note: 'Temporary placeholder for capacity and utilization summaries.',
  },
]

export default function SlotUsageSummary({ doctorId, selectedDate }) {
  const selectedDateLabel = selectedDate || 'a selected date'
  const doctorLabel = doctorId ? `Doctor ${doctorId}` : 'the selected doctor'

  return (
    <section className="slot-usage-summary" aria-labelledby="slot-usage-summary-title">
      <div className="slot-usage-summary__header">
        <div>
          <p className="slot-usage-summary__eyebrow">Temporary placeholder data</p>
          <h3 id="slot-usage-summary-title">Slot Usage Summary</h3>
          <p className="slot-usage-summary__context">
            {doctorLabel} for {selectedDateLabel}. Real slot counts will be wired in later without changing this layout.
          </p>
        </div>
        <span className="slot-usage-summary__badge">Mock values only</span>
      </div>

      <div className="slot-usage-summary__grid">
        {placeholderSections.map((section) => (
          <article className="slot-usage-summary__card" key={section.title}>
            <p className="slot-usage-summary__card-title">{section.title}</p>
            <strong className="slot-usage-summary__card-value">{section.value}</strong>
            <p className="slot-usage-summary__card-note">{section.note}</p>
          </article>
        ))}
      </div>

      <article className="slot-usage-summary__future">
        <div>
          <p className="slot-usage-summary__eyebrow">Future real availability data</p>
          <h4>Availability data placeholder</h4>
        </div>
        <p className="slot-usage-summary__future-copy">
          This section is reserved for actual availability totals, blocked intervals, and other scheduling signals once
          the counting logic is implemented.
        </p>
        <ul className="slot-usage-summary__future-list">
          <li>Daily availability totals</li>
          <li>Open versus blocked slot counts</li>
          <li>Capacity signals for future scheduling rules</li>
        </ul>
      </article>
    </section>
  )
}