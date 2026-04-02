import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppointmentTypeSelector from "../components/booking/AppointmentType";
import DateSelector from "../components/booking/DateSelector";
import TimeSlotsSelector from "../components/booking/TimeSlots";
import AppointmentConfirmation from "../components/booking/ConfirmationCard";
import defaultAvatar from "../assets/default-avatar.png";
import medicalPng from "../assets/medicalPng.png";
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
    {
      id: 1,
      name: "Normal appointment",
      title: "Normal appointment",
      description:
        "A standard visit to review your overall health, discuss any symptoms, and receive basic care or guidance.",
      image: medicalPng,
    },
    {
      id: 2,
      name: "Follow-up appointment",
      title: "Follow-up appointment",
      description:
        "Review previous treatment, discuss progress, and update the care plan if needed.",
      image: medicalPng,
    },
  ];

  const availableDates = useMemo(
    () => [
      new Date(2025, 8, 2),
      new Date(2025, 8, 5),
      new Date(2025, 8, 9),
      new Date(2025, 8, 10),
      new Date(2025, 8, 15),
      new Date(2025, 8, 16),
      new Date(2025, 8, 19),
      new Date(2025, 8, 23),
      new Date(2025, 8, 24),
      new Date(2025, 8, 29),
    ],
    []
  );

  const timeSlotsByDate = {
    "2025-09-02": [
      { time: "7:00 am", status: 1 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 0 },
      { time: "10:00 am", status: 1 },
      { time: "11:00 am", status: 1 },
      { time: "1:00 pm", status: 0 },
      { time: "2:00 pm", status: 0 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 1 },
      { time: "3:30 pm", status: 1 },
      { time: "4:00 pm", status: 0 },
      { time: "4:30 pm", status: 1 },
    ],
    "2025-09-05": [
      { time: "7:00 am", status: 1 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 0 },
      { time: "10:00 am", status: 1 },
      { time: "11:00 am", status: 1 },
      { time: "1:00 pm", status: 1 },
      { time: "2:00 pm", status: 1 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 0 },
      { time: "3:30 pm", status: 1 },
      { time: "4:00 pm", status: 0 },
      { time: "4:30 pm", status: 1 },
    ],
    "2025-09-09": [
      { time: "7:00 am", status: 0 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 0 },
      { time: "10:00 am", status: 1 },
      { time: "11:00 am", status: 0 },
      { time: "1:00 pm", status: 0 },
      { time: "2:00 pm", status: 1 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 0 },
      { time: "3:30 pm", status: 0 },
      { time: "4:00 pm", status: 1 },
      { time: "4:30 pm", status: 1 },
    ],
    "2025-09-10": [
      { time: "7:00 am", status: 1 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 0 },
      { time: "10:00 am", status: 0 },
      { time: "11:00 am", status: 0 },
      { time: "1:00 pm", status: 1 },
      { time: "2:00 pm", status: 1 },
      { time: "2:30 pm", status: 1 },
      { time: "3:00 pm", status: 0 },
      { time: "3:30 pm", status: 1 },
      { time: "4:00 pm", status: 1 },
      { time: "4:30 pm", status: 1 },
    ],
    "2025-09-15": [
      { time: "7:00 am", status: 0 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 1 },
      { time: "10:00 am", status: 1 },
      { time: "11:00 am", status: 1 },
      { time: "1:00 pm", status: 1 },
      { time: "2:00 pm", status: 1 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 0 },
      { time: "3:30 pm", status: 0 },
      { time: "4:00 pm", status: 0 },
      { time: "4:30 pm", status: 0 },
    ],
    "2025-09-16": [
      { time: "7:00 am", status: 1 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 0 },
      { time: "10:00 am", status: 0 },
      { time: "11:00 am", status: 0 },
      { time: "1:00 pm", status: 0 },
      { time: "2:00 pm", status: 0 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 1 },
      { time: "3:30 pm", status: 0 },
      { time: "4:00 pm", status: 1 },
      { time: "4:30 pm", status: 1 },
    ],
    "2025-09-19": [
      { time: "7:00 am", status: 1 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 1 },
      { time: "10:00 am", status: 1 },
      { time: "11:00 am", status: 1 },
      { time: "1:00 pm", status: 1 },
      { time: "2:00 pm", status: 1 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 1 },
      { time: "3:30 pm", status: 0 },
      { time: "4:00 pm", status: 0 },
      { time: "4:30 pm", status: 0 },
    ],
    "2025-09-23": [
      { time: "7:00 am", status: 0 },
      { time: "8:00 am", status: 0 },
      { time: "9:00 am", status: 0 },
      { time: "10:00 am", status: 0 },
      { time: "11:00 am", status: 0 },
      { time: "1:00 pm", status: 0 },
      { time: "2:00 pm", status: 0 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 0 },
      { time: "3:30 pm", status: 0 },
      { time: "4:00 pm", status: 0 },
      { time: "4:30 pm", status: 0 },
    ],
    "2025-09-24": [
      { time: "7:00 am", status: 1 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 1 },
      { time: "10:00 am", status: 1 },
      { time: "11:00 am", status: 1 },
      { time: "1:00 pm", status: 1 },
      { time: "2:00 pm", status: 1 },
      { time: "2:30 pm", status: 1 },
      { time: "3:00 pm", status: 1 },
      { time: "3:30 pm", status: 0 },
      { time: "4:00 pm", status: 0 },
      { time: "4:30 pm", status: 1 },
    ],
    "2025-09-29": [
      { time: "7:00 am", status: 1 },
      { time: "8:00 am", status: 1 },
      { time: "9:00 am", status: 0 },
      { time: "10:00 am", status: 1 },
      { time: "11:00 am", status: 1 },
      { time: "1:00 pm", status: 0 },
      { time: "2:00 pm", status: 0 },
      { time: "2:30 pm", status: 0 },
      { time: "3:00 pm", status: 0 },
      { time: "3:30 pm", status: 0 },
      { time: "4:00 pm", status: 0 },
      { time: "4:30 pm", status: 1 },
    ],
  };

  const formatDateKey = (date) => {
    if (!date) return "";
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const selectedDateKey = formatDateKey(selectedDate);
  const timeSlots = timeSlotsByDate[selectedDateKey] || [];

  const selectedType = appointmentTypes.find(
    (type) => type.id === selectedTypeId
  );

  const handleDateSelect = (date) => {
    if (!date) return;
    setSelectedDate(date);
    setSelectedTime(null);
  };

  const handleCancel = () => {
    navigate(-1);
  };

  const handleConfirm = () => {
  navigate("/appointment-success", {
    state: {
      patientName: user.name,
      appointmentType: selectedType?.title || selectedType?.name,
      selectedDate,
      selectedTime,
    },
  });
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

          <AppointmentTypeSelector
            types={appointmentTypes}
            selectedTypeId={selectedTypeId}
            onSelect={(type) => setSelectedTypeId(type.id)}
          />
        </section>

        <section className="date-time-section">
          <div className="date-column">
            <h2 className="section-title">Available dates:</h2>
            <p className="section-subtitle">Choose a date.</p>

            <div className="content-card">
              <DateSelector
                selectedDate={selectedDate}
                availableDates={availableDates}
                onSelect={handleDateSelect}
              />
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

              <TimeSlotsSelector
                timeSlots={timeSlots}
                selectedTime={selectedTime}
                onSelect={setSelectedTime}
              />
            </div>
          </div>
        </section>

        <section className="confirmation-section">
          <AppointmentConfirmation
            appointmentType={selectedType?.title || selectedType?.name}
            selectedDate={selectedDate}
            selectedTime={selectedTime}
            onCancel={handleCancel}
            onConfirm={handleConfirm}
          />
        </section>
      </div>
    </div>
  );
}