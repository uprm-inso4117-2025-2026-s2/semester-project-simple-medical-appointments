import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";
import "./styles/TimeSlots.css";

export default function DateSelector({
  availableDates = [],
  selectedDate,
  onSelect,
}) {
  return (
    <div className="date-selector">
      <DayPicker
        mode="single"
        selected={selectedDate}
        onSelect={onSelect}
        animate
        captionLayout="label"
        month={selectedDate || new Date(2025, 8, 1)}
        navLayout="around"
        required
        timeZone="America/La_Paz"
        weekStartsOn={0}
        disabled={[
          { before: new Date(2025, 8, 1) },
          (date) =>
            !availableDates.some(
              (availableDate) =>
                availableDate.getFullYear() === date.getFullYear() &&
                availableDate.getMonth() === date.getMonth() &&
                availableDate.getDate() === date.getDate()
            ),
        ]}
      />
    </div>
  );
}