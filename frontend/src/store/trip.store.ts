import { create } from 'zustand';
import { Trip, Itinerary, ItineraryItem } from '../types/api.types';

interface TripState {
  trips: Trip[];
  currentTrip: Trip | null;
  isLoading: boolean;
  error: string | null;
}

interface TripActions {
  setTrips: (trips: Trip[]) => void;
  addTrip: (trip: Trip) => void;
  updateTrip: (id: string, updates: Partial<Trip>) => void;
  deleteTrip: (id: string) => void;
  setCurrentTrip: (trip: Trip | null) => void;
  addItinerary: (tripId: string, itinerary: Itinerary) => void;
  updateItinerary: (tripId: string, itineraryId: string, updates: Partial<Itinerary>) => void;
  deleteItinerary: (tripId: string, itineraryId: string) => void;
  addActivity: (tripId: string, itineraryId: string, activity: ItineraryItem) => void;
  updateActivity: (tripId: string, itineraryId: string, activityId: string, updates: Partial<ItineraryItem>) => void;
  deleteActivity: (tripId: string, itineraryId: string, activityId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useTripStore = create<TripState & TripActions>((set, get) => ({
  // State
  trips: [],
  currentTrip: null,
  isLoading: false,
  error: null,

  // Actions
  setTrips: (trips) => set({ trips }),

  addTrip: (trip) => {
    const { trips } = get();
    set({ trips: [...trips, trip] });
  },

  updateTrip: (id, updates) => {
    const { trips } = get();
    set({
      trips: trips.map((trip) => (trip.id === id ? { ...trip, ...updates } : trip)),
    });
  },

  deleteTrip: (id) => {
    const { trips } = get();
    set({ trips: trips.filter((trip) => trip.id !== id) });
  },

  setCurrentTrip: (trip) => set({ currentTrip: trip }),

  addItinerary: (tripId, itinerary) => {
    const { trips } = get();
    set({
      trips: trips.map((trip) =>
        trip.id === tripId
          ? {
              ...trip,
              itineraries: [...(trip.itineraries || []), itinerary],
            }
          : trip
      ),
    });
  },

  updateItinerary: (tripId, itineraryId, updates) => {
    const { trips } = get();
    set({
      trips: trips.map((trip) =>
        trip.id === tripId
          ? {
              ...trip,
              itineraries: (trip.itineraries || []).map((it: Itinerary) =>
                it.id === itineraryId ? { ...it, ...updates } : it
              ),
            }
          : trip
      ),
    });
  },

  deleteItinerary: (tripId, itineraryId) => {
    const { trips } = get();
    set({
      trips: trips.map((trip) =>
        trip.id === tripId
          ? {
              ...trip,
              itineraries: (trip.itineraries || []).filter((it: Itinerary) => it.id !== itineraryId),
            }
          : trip
      ),
    });
  },

  addActivity: (tripId, itineraryId, activity) => {
    const { trips } = get();
    set({
      trips: trips.map((trip) =>
        trip.id === tripId
          ? {
              ...trip,
              itineraries: (trip.itineraries || []).map((it: Itinerary) =>
                it.id === itineraryId
                  ? { ...it, items: [...(it.items || []), activity] }
                  : it
              ),
            }
          : trip
      ),
    });
  },

  updateActivity: (tripId, itineraryId, activityId, updates) => {
    const { trips } = get();
    set({
      trips: trips.map((trip) =>
        trip.id === tripId
          ? {
              ...trip,
              itineraries: (trip.itineraries || []).map((it: Itinerary) =>
                it.id === itineraryId
                  ? {
                      ...it,
                      items: (it.items || []).map((act: ItineraryItem) =>
                        act.id === activityId ? { ...act, ...updates } : act
                      ),
                    }
                  : it
              ),
            }
          : trip
      ),
    });
  },

  deleteActivity: (tripId, itineraryId, activityId) => {
    const { trips } = get();
    set({
      trips: trips.map((trip) =>
        trip.id === tripId
          ? {
              ...trip,
              itineraries: (trip.itineraries || []).map((it: Itinerary) =>
                it.id === itineraryId
                  ? {
                      ...it,
                      items: (it.items || []).filter((act: ItineraryItem) => act.id !== activityId),
                    }
                  : it
              ),
            }
          : trip
      ),
    });
  },

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),
}));
