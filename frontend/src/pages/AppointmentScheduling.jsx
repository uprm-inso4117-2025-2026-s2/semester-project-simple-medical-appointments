import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import defaultAvatar from "../assets/default-avatar.png";
import "../styles/AppointmentScheduling.css";

export default function AppointmentSchedule() {
  const navigate = useNavigate();

  const [selectedTypeId, setSelectedTypeId] = useState(1);
  const [selectedDate, setSelectedDate] = useState(new Date(2025, 8, 5));
  const [selectedTime, setSelectedTime] = useState(null);

  const user = {
    name: "Patient Name",
    profileImage: null,
  };

  const appointmentTypes = [
  ];

  const timeSlotsByDate = {
  };

  const formatDateKey = (date) => {

  };



  return (
    <div className="appointment-page">
      <div className="appointment-shell">
        <header className="appointment-header">
          <div className="appointment-header-left">
            <h1 className="patient-name">{user.name}</h1>
          </div>

          <div className="profile-icon-box">
            <img
              src={user.profileImage || defaultAvatar}
              alt={`${user.name} profile`}
              className="profile-image"
              onError={(e) => {
                e.target.src = defaultAvatar;
              }}
            />
          </div>
        </header>

        <section className="appointment-type-section">
          <h2 className="section-title">Choose an appointment:</h2>

        </section>

        <section className="date-time-section">
          <div className="date-column">
            <h2 className="section-title">Available dates:</h2>
            <p className="section-subtitle">Choose a date.</p>

            <div className="content-card">

            </div>
          </div>

          <div className="time-column">
            <h2 className="section-title">Available time slots:</h2>
            <p className="section-subtitle">Choose a time.</p>

            <div className="content-card">
              <p className="selected-date-label">
                {selectedDate
                  ? `Showing time slots for ${selectedDate.toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}`
                  : "Select a date to view available time slots."}
              </p>

            </div>
          </div>
        </section>

        <section className="confirmation-section">

        </section>
      </div>
    </div>
  );
}