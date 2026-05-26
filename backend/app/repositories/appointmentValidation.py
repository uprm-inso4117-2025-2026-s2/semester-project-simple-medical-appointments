"""Scheduling: Appointment validation - conflict detection for appointment creation"""

from datetime import datetime
from ..supabase import supabase

def appointmentOverlap(doctorID: str, startTime: datetime, endTime: datetime) -> bool:
    #Verifies if a new appointment overlaps with existing appointments for the same doctor

    if startTime >= endTime: #blocks invalid appointments where start time is after end time
        raise ValueError("Start time must be before end time") #shows backend error
    
    response = supabase.table("appointments").select("*").eq("doctorID", doctorID).lt("startTime", endTime).gt("endTime", startTime).execute() #stores result from database search, selecting the appointmet column for the same doctor and existing appointments starts before the new one ends while confirming the appintment ends before a new one starts
    return len(response.data) > 0 #true if at least one appointment overlap was found

def validateAppointment(doctorID: str, startTime: datetime, endTime: datetime):
    hasConflict = appointmentOverlap(doctorID, startTime, endTime) #check if appointment conflicts with another one

    if hasConflict: #if conflict is found, raise an error
        raise ValueError("Appointment time conflicts with an existing appointment") #shows backend error if there is a conflict
    
    supabase.table("appointments").insert({"doctorID": doctorID, "startTime": startTime, "endTime": endTime}).execute() #if no conflict is found, insert the new appointment into the database


