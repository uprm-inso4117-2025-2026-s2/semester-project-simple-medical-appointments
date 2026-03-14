import { useState } from "react"
import { submitPatientForm } from "../services/api"

function PatientForm() {
  const [formData, setFormData] = useState({
    name: "",
    surname: "",
    symptoms: "",
    medications: ""
  })

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      await submitPatientForm(formData)
      alert("Form submitted successfully")
    } catch (error) {
      console.error(error)
      alert("Submission failed")
    }
  }

  return (
    <div className="form-page">

      {/* Top Navigation */}
      <div className="form-header">
        <button className="back-button">Back</button>
        <h1>Form Submission</h1>
        <div className="profile-icon">👤</div>
      </div>

      {/* Instructions */}
      <p className="form-instructions">Fill all required areas</p>

      {/* Form Card */}
      <div className="form-card">

        <form onSubmit={handleSubmit}>

          <label>Name</label>
          <input
            type="text"
            name="name"
            placeholder="Value"
            value={formData.name}
            onChange={handleChange}
            required
          />

          <label>Surname</label>
          <input
            type="text"
            name="surname"
            placeholder="Value"
            value={formData.surname}
            onChange={handleChange}
            required
          />

          <label>Symptoms and/or Allergies</label>
          <input
            type="text"
            name="symptoms"
            placeholder="Value"
            value={formData.symptoms}
            onChange={handleChange}
          />

          <label>Medications</label>
          <textarea
            name="medications"
            placeholder="Value"
            value={formData.medications}
            onChange={handleChange}
          />

          <button type="submit" className="submit-button">
            Submit
          </button>

        </form>

      </div>

    </div>
  )
}

export default PatientForm