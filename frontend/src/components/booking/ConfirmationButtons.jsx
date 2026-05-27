import { useNavigate } from "react-router-dom";
import "./styles/ConfirmationButtons.css";

export default function ConfirmationButtons({
  onCancel,
  onConfirm,
  confirmText = "Confirm",
  cancelText = "Cancel",
  disabled = false,
  loading = false,
}) {
  const navigate = useNavigate();

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      navigate(-1); 
    }
  };

  return (
    <div className="confirmation-buttons">
      <button
        type="button"
        className="confirmation-button cancel"
        onClick={handleCancel}
        disabled={loading}
      >
        {cancelText}
      </button>

      <button
        type="button"
        className="confirmation-button confirm"
        onClick={onConfirm}
        disabled={disabled || loading}
      >
        {loading ? "Processing..." : confirmText}
      </button>
    </div>
  );
}