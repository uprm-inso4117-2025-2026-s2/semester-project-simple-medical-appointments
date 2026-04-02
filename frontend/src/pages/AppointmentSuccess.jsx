import { useLocation, useNavigate } from "react-router-dom";
import defaultAvatar from "../assets/default-avatar.png";
import "../styles/AppointmentSuccess.css";

export default function AppointmentSuccess() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    patientName = "Patient Name",
    selectedDate = null,
    selectedTime = "",
  } = location.state || {};

  const formatDate = (date) => {
    if (!date) return "";

    return new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    }).format(new Date(date));
  };

  return (
    <div className="appointment-success-page">
      <div className="appointment-success-shell">
        <header className="appointment-success-header">
          <div className="appointment-success-header-left">
            <h1 className="appointment-success-patient-name">{patientName}</h1>
          </div>

          <div className="appointment-success-profile-icon-box">
            <img
              src={defaultAvatar}
              alt="Profile"
              className="appointment-success-profile-image"
            />
          </div>
        </header>

        <section className="appointment-success-content">
          <div className="appointment-success-card">
            <div className="appointment-success-icon">✓</div>

            <h2 className="appointment-success-title">
              Appointment Successfully Booked!
            </h2>

            <p className="appointment-success-text">
              Your appointment has been booked for {formatDate(selectedDate)}
              {selectedTime ? ` at ${selectedTime}` : "."}
            </p>
          </div>

          <button
            type="button"
            className="appointment-success-home-button"
            onClick={() => navigate("/")}
          >
            Return back to home page
          </button>
        </section>
      </div>
    </div>
  );
}