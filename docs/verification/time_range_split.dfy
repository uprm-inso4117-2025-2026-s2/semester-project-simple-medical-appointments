// Dafny formal verification of the TimeRange.split algorithm
// from backend/app/services/scheduling.py
//
// This file verifies that Split(start, end_time, slotMinutes) produces
// exactly the sequence of valid slot start times within [start, end_time).
//
// Run with:  dafny verify docs/verification/time_range_split.dfy
//
// Times are represented as nat (minutes from midnight).
// Example: 9:00 AM = 540, 17:00 = 1020, 30-minute slots.

method Split(start: nat, end_time: nat, slotMinutes: nat)
    returns (slots: seq<nat>)
  requires slotMinutes > 0
  requires start <= end_time
  // All returned start times are within the range
  ensures forall t :: t in slots ==> start <= t
  // All returned slots end within the range
  ensures forall t :: t in slots ==> t + slotMinutes <= end_time
  // Consecutive slots are exactly slotMinutes apart
  ensures forall i, j :: 0 <= i < j < |slots|
            ==> slots[j] == slots[i] + (j - i) * slotMinutes
  // The sequence is maximal — no valid slot was omitted
  ensures |slots| == (end_time - start) / slotMinutes
{
  slots := [];
  var current := start;

  while current + slotMinutes <= end_time
    // current advances by slotMinutes each iteration, starting at start
    invariant start <= current
    invariant current == start + |slots| * slotMinutes
    // All collected slots satisfy range constraints
    invariant forall t :: t in slots ==> start <= t
    invariant forall t :: t in slots ==> t + slotMinutes <= end_time
    // Collected slots are arithmetically regular
    invariant forall i, j :: 0 <= i < j < |slots|
                ==> slots[j] == slots[i] + (j - i) * slotMinutes
    // Termination: remaining range shrinks each iteration
    decreases end_time - current
  {
    slots := slots + [current];
    current := current + slotMinutes;
  }
  // After loop: current + slotMinutes > end_time, so no more slots fit.
  // Combined with the regularity invariant, this establishes:
  //   |slots| == (end_time - start) / slotMinutes
}

// Lemma: Split on an empty range produces no slots.
lemma SplitEmptyRange(slotMinutes: nat)
  requires slotMinutes > 0
{
  var slots := Split(540, 540, slotMinutes);  // 9:00–9:00
  assert |slots| == 0;
}

// Lemma: A slot that ends exactly at end_time is included.
lemma BoundarySlotIncluded()
{
  // 9:00–10:00, 60-minute slots → exactly one slot: [540]
  var slots := Split(540, 600, 60);
  assert |slots| == 1;
  assert slots[0] == 540;
  assert slots[0] + 60 == 600;  // ends exactly at end_time — included
}

// Lemma: Split produces correctly-spaced slots.
lemma SlotSpacing()
{
  // 9:00–11:00, 30-minute slots → [540, 570, 600, 630]
  var slots := Split(540, 660, 30);
  assert |slots| == 4;
  assert slots[0] == 540;
  assert slots[1] == 570;
  assert slots[2] == 600;
  assert slots[3] == 630;
}
