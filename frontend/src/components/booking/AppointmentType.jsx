import React from "react";
import "./styles/AppointmentType.css";

// Current expected data format:
// const appointmentTypes = [
//   {
//     id: 1,
//     title: "Normal appointment",
//     description:
//       "Appointment description",
//     image: medicalPng,
//   },
// ];

function AppointmentTypeSelector({
  types = [],
  selectedTypeId,
  onSelect,
  loading = false,
  error = null,
}) {
  if (loading) {
    return (
      <div className="booking-section">
        <p>Loading appointment types...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="booking-section">
        <p className="appointment-type-error">Error loading appointments</p>
      </div>
    );
  }

  if (!types.length) {
    return (
      <div className="booking-section">
        <p>No appointment available</p>
      </div>
    );
  }

  return (
    <div className="booking-section">
      <div className="appointment-type-list">
        {types.map((type) => {
          const isSelected = selectedTypeId === type.id;

          return (
            <button
              key={type.id}
              type="button"
              disabled={type.disabled}
              onClick={() => onSelect(type)}
              className={`appointment-type-card ${isSelected ? "selected" : ""}`}
            >
              <div className="appointment-type-image-wrapper">
                <img
                  src={type.image}
                  alt={type.title || type.name}
                  className="appointment-type-image"
                />
              </div>

              <div className="appointment-type-content">
                <h3 className="appointment-type-title">
                  {type.title || type.name}
                </h3>

                {type.description && (
                  <p className="appointment-type-description">
                    {type.description}
                  </p>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default AppointmentTypeSelector;