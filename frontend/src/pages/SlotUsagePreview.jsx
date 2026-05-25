import SlotUsageSummary from '../components/SlotUsageSummary'

export default function SlotUsagePreview() {
  // Provide mock props to the placeholder component so it renders a concrete preview.
  return (
    <main style={{ padding: '2rem' }}>
      <h2>Slot Usage Summary Preview</h2>
      <div style={{ maxWidth: 980 }}>
        <SlotUsageSummary doctorId={123} selectedDate={'2026-05-23'} />
      </div>
    </main>
  )
}
