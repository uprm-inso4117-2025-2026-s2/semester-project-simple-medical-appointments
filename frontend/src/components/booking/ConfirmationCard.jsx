import "./styles/ConfirmationCard.css";

export default function AppointmentConfirmation({
  appointmentType = "",
  selectedDate = null,
  selectedTime = "",
  onCancel,
  onConfirm,
}) {
  const formatDate = (date) => {
    if (!date) return "";

    return new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(date);
  };

  const confirmationText = `Book ${ //removed the extra appointment in the confirmation card text
    appointmentType || "appointment"
  } ${
    selectedDate ? `on ${formatDate(selectedDate)}` : ""
  } ${
    selectedTime ? `at ${selectedTime}` : ""
  }?`;

  return (
    <div className="appointment-confirmation">
      <h2 className="appointment-confirmation-title">
        Confirm appointment details:
      </h2>

      <p className="appointment-confirmation-text">{confirmationText}</p>

      <div className="appointment-confirmation-actions">
        <button
          type="button"
          className="appointment-confirmation-button cancel"
          onClick={onCancel}
        >
          Cancel
        </button>

        <button
          type="button"
          className="appointment-confirmation-button confirm"
          onClick={onConfirm}
        >
          Confirm
        </button>
      </div>
    </div>
  );
}