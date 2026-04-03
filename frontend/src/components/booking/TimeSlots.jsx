import "./styles/TimeSlots.css";

export default function TimeSlotsSelector({
  timeSlots = [],
  selectedTime = null,
  onSelect,
  loading = false,
}) {
  if (loading) {
    return <p className="time-slots-message">Loading available times...</p>;
  }

  if (!timeSlots.length) {
    return <p className="time-slots-message">No time slots found for this date.</p>;
  }

  return (
    <div className="time-slots-container">
      {timeSlots.map((slot, index) => {
        const isUnavailable = slot.status === 1;
        const isSelected = selectedTime === slot.time;

        return (
          <button
            key={`${slot.time}-${index}`}
            type="button"
            className={`time-slot-button 
              ${isSelected ? "selected" : ""} 
              ${isUnavailable ? "unavailable" : ""}`}
            onClick={() => {
              if (!isUnavailable) {
                onSelect?.(slot.time);
              }
            }}
            disabled={isUnavailable}
          >
            {slot.time}
          </button>
        );
      })}
    </div>
  );
}