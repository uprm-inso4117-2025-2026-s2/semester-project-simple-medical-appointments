import { useState, useEffect } from "react";
import { supabase } from "../lib/supabaseClient";

export default function ServiceCatalog() {
  const [services, setServices] = useState([]);
  const [name, setName] = useState("");
  const [duration, setDuration] = useState("");
  useEffect(() => {
    fetchServices();
  }, []);
  
  const fetchServices = async () => {
    const { data, error } = await supabase
      .from("services")
      .select("*")
      .order("created_at", { ascending: false });
  
    if (error) {
      console.error("Error fetching services:", error);
    } else {
      setServices(data);
    }
  };

  const handleCreateService = async () => {
    if (!name || !duration) return;
  
    const { error } = await supabase.from("services").insert([
      {
        name,
        duration: Number(duration),
        is_active: true,
      },
    ]);
  
    if (error) {
      console.error("Error creating service:", error);
    } else {
      fetchServices();
      setName("");
      setDuration("");
    }
  };

  

  const toggleServiceStatus = async (id, currentStatus) => {
    const { error } = await supabase
      .from("services")
      .update({ is_active: !currentStatus })
      .eq("id", id);
  
    if (error) {
      console.error("Error updating service:", error);
    } else {
      fetchServices();
    }
  };

  const handleEditService = (id) => {
    const newName = prompt("Enter new service name:");
    const newDuration = prompt("Enter new duration (minutes):");

    if (!newName || !newDuration) return;

    setServices(
      services.map((service) =>
        service.id === id
          ? { ...service, name: newName, duration: Number(newDuration) }
          : service
      )
    );
  };

  return (
    <div>
      <h2>Service Catalog</h2>

      <input
        type="text"
        placeholder="Service Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      <input
        type="number"
        placeholder="Duration (minutes)"
        value={duration}
        onChange={(e) => setDuration(e.target.value)}
      />

      <button onClick={handleCreateService}>
        Add Service
      </button>

      <hr />

      {services.map((service) => (
        <div key={service.id}>
          <strong>{service.name}</strong> — {service.duration} min —{" "}
          {service.is_active ? "Active" : "Inactive"}

          <button onClick={() => toggleServiceStatus(service.id, service.is_active)}>
            Toggle Active
          </button>

          <button onClick={() => handleEditService(service.id)}>
            Edit
          </button>
        </div>
      ))}
    </div>
  );
}